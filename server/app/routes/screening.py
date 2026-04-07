"""Screening routes - Batch candidate screening API"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.models import get_db, Job, MatchResult
from app.services.screening import (
    ScreeningCriteria,
    batch_screen_candidates,
    batch_accept_candidates,
    batch_reject_candidates,
    get_screening_stats,
)

router = APIRouter()


# Request models
class ScreeningCriteriaRequest(BaseModel):
    min_total_score: float = 0.5
    min_skill_score: float = 0.4
    min_experience_score: float = 0.3
    min_education_score: float = 0.3
    exclude_rejected: bool = True
    use_llm_evaluation: bool = False


class BatchActionRequest(BaseModel):
    match_ids: List[int]
    target_status: Optional[str] = "screening"


# Response helpers
def screening_result_to_response(result) -> dict:
    """Convert screening result to response dict"""
    return {
        "match_id": result.match_id,
        "candidate_id": result.candidate_id,
        "candidate_name": result.candidate_name,
        "total_score": result.total_score,
        "passed": result.passed,
        "reasons": result.reasons,
        "llm_evaluation": result.llm_evaluation,
        "interview_questions": result.interview_questions,
    }


@router.post("/{job_id}/screen")
async def screen_candidates(
    job_id: int,
    criteria: Optional[ScreeningCriteriaRequest] = None,
    candidate_ids: Optional[List[int]] = None,
    db: Session = Depends(get_db)
):
    """Run batch screening for candidates of a job"""
    # Check job exists
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return {"error": "Job not found"}, 404
    
    # Build criteria
    screening_criteria = None
    if criteria:
        screening_criteria = ScreeningCriteria(
            min_total_score=criteria.min_total_score,
            min_skill_score=criteria.min_skill_score,
            min_experience_score=criteria.min_experience_score,
            min_education_score=criteria.min_education_score,
            exclude_rejected=criteria.exclude_rejected,
            use_llm_evaluation=criteria.use_llm_evaluation,
        )
    
    # Run screening
    results = await batch_screen_candidates(db, job_id, screening_criteria, candidate_ids)
    
    passed = [r for r in results if r.passed]
    failed = [r for r in results if not r.passed]
    
    return {
        "job_id": job_id,
        "total": len(results),
        "passed": len(passed),
        "failed": len(failed),
        "results": [screening_result_to_response(r) for r in results],
    }


@router.get("/{job_id}/stats")
async def get_job_screening_stats(job_id: int, db: Session = Depends(get_db)):
    """Get screening statistics for a job"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return {"error": "Job not found"}, 404
    
    stats = get_screening_stats(db, job_id)
    return {"job_id": job_id, **stats}


@router.post("/{job_id}/accept")
async def batch_accept(
    job_id: int,
    data: BatchActionRequest,
    db: Session = Depends(get_db)
):
    """Batch accept candidates"""
    result = await batch_accept_candidates(data.match_ids, data.target_status)
    return {"job_id": job_id, **result}


@router.post("/{job_id}/reject")
async def batch_reject(
    job_id: int,
    data: BatchActionRequest,
    db: Session = Depends(get_db)
):
    """Batch reject candidates"""
    result = await batch_reject_candidates(data.match_ids)
    return {"job_id": job_id, **result}


@router.post("/{job_id}/filter-excellent")
async def filter_excellent_candidates(
    job_id: int,
    threshold: float = 0.8,
    db: Session = Depends(get_db)
):
    """快速筛选优秀候选人 (分数 >= threshold)"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return {"error": "Job not found"}, 404
    
    matches = db.query(MatchResult).filter(
        MatchResult.job_id == job_id,
        MatchResult.total_score >= threshold,
    ).order_by(MatchResult.total_score.desc()).all()
    
    return {
        "job_id": job_id,
        "threshold": threshold,
        "count": len(matches),
        "matches": [
            {
                "id": m.id,
                "candidate_id": m.candidate_id,
                "total_score": m.total_score,
            }
            for m in matches
        ]
    }