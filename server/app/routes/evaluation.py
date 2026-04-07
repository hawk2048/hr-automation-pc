"""HR Automation - Evaluation API Routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.database import get_db
from app.models import Job, Candidate, MatchResult
from app.services import evaluation


router = APIRouter()


class EvaluateCandidateRequest(BaseModel):
    job_id: int
    candidate_id: int


class GenerateQuestionsRequest(BaseModel):
    job_id: int
    candidate_id: int
    num_questions: int = 5


@router.post("/evaluate")
async def evaluate_candidate(
    request: EvaluateCandidateRequest,
    db: Session = Depends(get_db)
):
    """Use LLM to deeply evaluate a candidate for a job"""
    # Get job
    job = db.query(Job).filter(Job.id == request.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get candidate
    candidate = db.query(Candidate).filter(Candidate.id == request.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Parse job data
    import json
    job_qual = json.loads(job.qualifications) if job.qualifications else {}
    job_skills = json.loads(job.skills) if job.skills else {}
    
    job_requirements = {
        **job_qual,
        "hard_skills": job_skills.get("hard_skills", []),
        "soft_skills": job_skills.get("soft_skills", []),
    }
    
    # Prepare candidate info
    candidate_info = {
        "name": candidate.name,
        "email": candidate.email,
        "phone": candidate.phone,
    }
    
    # Get LLM evaluation
    result = await evaluation.evaluate_candidate_with_llm(
        job_title=job.title,
        job_description=job.description or "",
        job_requirements=job_requirements,
        candidate_info=candidate_info,
        candidate_resume=candidate.resume_text or "",
    )
    
    if result.get("success"):
        return {
            "success": True,
            "evaluation": result["evaluation"],
        }
    else:
        return {
            "success": False,
            "error": result.get("error", "Evaluation failed"),
            "raw_response": result.get("raw_response"),
        }


@router.post("/questions")
async def generate_interview_questions(
    request: GenerateQuestionsRequest,
    db: Session = Depends(get_db)
):
    """Generate tailored interview questions"""
    job = db.query(Job).filter(Job.id == request.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    candidate = db.query(Candidate).filter(Candidate.id == request.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    import json
    job_qual = json.loads(job.qualifications) if job.qualifications else {}
    job_skills = json.loads(job.skills) if job.skills else {}
    
    job_requirements = {
        **job_qual,
        "hard_skills": job_skills.get("hard_skills", []),
        "soft_skills": job_skills.get("soft_skills", []),
    }
    
    candidate_background = f"{candidate.name}\n{candidate.resume_text[:1000]}" if candidate.resume_text else candidate.name
    
    result = await evaluation.generate_interview_questions(
        job_title=job.title,
        job_requirements=job_requirements,
        candidate_background=candidate_background,
        num_questions=request.num_questions,
    )
    
    return result


@router.get("/summary/{candidate_id}")
async def get_candidate_summary(
    candidate_id: int,
    db: Session = Depends(get_db)
):
    """Generate LLM summary of candidate"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Get recent match results
    matches = db.query(MatchResult).filter(
        MatchResult.candidate_id == candidate_id
    ).order_by(MatchResult.total_score.desc()).limit(5).all()
    
    match_scores = [
        {
            "job_id": m.job_id,
            "score": m.total_score,
            "skill_score": m.skill_score,
            "experience_score": m.experience_score,
        }
        for m in matches
    ]
    
    candidate_info = {
        "name": candidate.name,
        "email": candidate.email,
        "phone": candidate.phone,
    }
    
    summary = await evaluation.generate_candidate_summary(
        candidate_info=candidate_info,
        resume_text=candidate.resume_text or "",
        match_results=match_scores,
    )
    
    return {"summary": summary}