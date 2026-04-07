"""Match routes"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
import json

from app.models import get_db, Job, Candidate, MatchResult
from app.schemas import MatchResultResponse, MatchResultUpdate
from app.errors import NotFoundError
from app.services.matching import match_job_to_candidates

router = APIRouter()


def match_to_response(match: MatchResult, db: Session) -> dict:
    """Convert MatchResult to response with candidate info"""
    candidate = db.query(Candidate).filter(Candidate.id == match.candidate_id).first()
    
    return {
        "id": match.id,
        "job_id": match.job_id,
        "candidate_id": match.candidate_id,
        "total_score": match.total_score,
        "skill_score": match.skill_score,
        "experience_score": match.experience_score,
        "semantic_score": match.semantic_score,
        "education_score": match.education_score,
        "salary_score": match.salary_score,
        "soft_skill_score": match.soft_skill_score,
        "llm_analysis": match.llm_analysis,
        "status": match.status,
        "created_at": match.created_at,
        "candidate_name": candidate.name if candidate else None,
        "candidate_location": candidate.location if candidate else None,
    }


@router.post("/{job_id}/match")
async def run_match(
    job_id: int,
    top_n: int = 20,
    candidate_ids: List[int] = None,
    db: Session = Depends(get_db)
):
    """Run matching for a job"""
    # Check job exists
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise NotFoundError("Job", job_id)
    
    results = await match_job_to_candidates(db, job_id, candidate_ids, top_n)
    
    return {
        "job_id": job_id,
        "matches": [match_to_response(m, db) for m in results],
        "total": len(results)
    }


@router.get("/{job_id}/results", response_model=List[dict])
async def get_match_results(
    job_id: int,
    status: str = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get match results for a job"""
    # Check job exists
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise NotFoundError("Job", job_id)
    
    query = db.query(MatchResult).filter(MatchResult.job_id == job_id)
    
    if status:
        query = query.filter(MatchResult.status == status)
    
    results = query.order_by(MatchResult.total_score.desc()).limit(limit).all()
    
    return [match_to_response(m, db) for m in results]


@router.get("/result/{result_id}")
async def get_match_result(result_id: int, db: Session = Depends(get_db)):
    """Get a specific match result"""
    match = db.query(MatchResult).filter(MatchResult.id == result_id).first()
    if not match:
        raise NotFoundError("Match Result", result_id)
    
    result = match_to_response(match, db)
    
    # Add candidate details
    candidate = db.query(Candidate).filter(Candidate.id == match.candidate_id).first()
    if candidate:
        result["candidate"] = {
            "id": candidate.id,
            "name": candidate.name,
            "email": candidate.email,
            "phone": candidate.phone,
            "location": candidate.location,
            "education": json.loads(candidate.education) if candidate.education else [],
            "work_experience": json.loads(candidate.work_experience) if candidate.work_experience else [],
            "skills": json.loads(candidate.skills) if candidate.skills else None,
            "salary_expectation": json.loads(candidate.salary_expectation) if candidate.salary_expectation else None,
            "availability": candidate.availability,
        }
    
    return result


@router.patch("/{match_id}/status")
async def update_match_status(
    match_id: int,
    data: MatchResultUpdate,
    db: Session = Depends(get_db)
):
    """Update match status"""
    match = db.query(MatchResult).filter(MatchResult.id == match_id).first()
    if not match:
        raise NotFoundError("Match Result", match_id)
    
    match.status = data.status
    db.commit()
    db.refresh(match)
    
    # Also update candidate status
    candidate = db.query(Candidate).filter(Candidate.id == match.candidate_id).first()
    if candidate and data.status in ["accepted", "rejected"]:
        candidate.status = "interview" if data.status == "accepted" else "rejected"
        db.commit()
    
    return match_to_response(match, db)