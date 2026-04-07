"""Candidate routes"""
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import json

from app.models import get_db, Candidate
from app.schemas import CandidateCreate, CandidateUpdate, CandidateResponse, FileUploadResponse
from app.errors import NotFoundError
from app.config import settings

router = APIRouter()


def candidate_to_response(candidate: Candidate) -> CandidateResponse:
    """Convert Candidate model to schema"""
    return CandidateResponse(
        id=candidate.id,
        name=candidate.name,
        email=candidate.email,
        phone=candidate.phone,
        location=candidate.location,
        education=json.loads(candidate.education) if candidate.education else [],
        work_experience=json.loads(candidate.work_experience) if candidate.work_experience else [],
        skills=json.loads(candidate.skills) if candidate.skills else None,
        salary_expectation=json.loads(candidate.salary_expectation) if candidate.salary_expectation else None,
        availability=candidate.availability,
        experience_years=candidate.experience_years,
        status=candidate.status,
        created_at=candidate.created_at,
        updated_at=candidate.updated_at,
    )


@router.post("/", response_model=CandidateResponse)
async def create_candidate(candidate_data: CandidateCreate, db: Session = Depends(get_db)):
    """Create a new candidate"""
    db_candidate = Candidate(
        name=candidate_data.name,
        email=candidate_data.email,
        phone=candidate_data.phone,
        location=candidate_data.location,
        education=json.dumps([e.model_dump() for e in candidate_data.education]) if candidate_data.education else None,
        work_experience=json.dumps([w.model_dump() for w in candidate_data.work_experience]) if candidate_data.work_experience else None,
        skills=json.dumps(candidate_data.skills) if candidate_data.skills else None,
        salary_expectation=json.dumps(candidate_data.salary_expectation) if candidate_data.salary_expectation else None,
        availability=candidate_data.availability,
        resume_text=candidate_data.resume_text,
        experience_years=candidate_data.experience_years,
    )
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    return candidate_to_response(db_candidate)


@router.get("/", response_model=List[CandidateResponse])
async def list_candidates(
    status: str = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List candidates"""
    query = db.query(Candidate)
    if status:
        query = query.filter(Candidate.status == status)
    candidates = query.order_by(Candidate.created_at.desc()).limit(limit).offset(offset).all()
    return [candidate_to_response(c) for c in candidates]


@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    """Get a candidate by ID"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise NotFoundError("Candidate", candidate_id)
    return candidate_to_response(candidate)


@router.patch("/{candidate_id}", response_model=CandidateResponse)
async def update_candidate(
    candidate_id: int,
    data: CandidateUpdate,
    db: Session = Depends(get_db)
):
    """Update a candidate"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise NotFoundError("Candidate", candidate_id)
    
    if data.name is not None:
        candidate.name = data.name
    if data.email is not None:
        candidate.email = data.email
    if data.phone is not None:
        candidate.phone = data.phone
    if data.location is not None:
        candidate.location = data.location
    if data.status is not None:
        candidate.status = data.status
    
    db.commit()
    db.refresh(candidate)
    return candidate_to_response(candidate)


@router.delete("/{candidate_id}")
async def delete_candidate(candidate_id: int, db: Session = Depends(get_db)):
    """Delete a candidate"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise NotFoundError("Candidate", candidate_id)
    
    db.delete(candidate)
    db.commit()
    return {"message": "Candidate deleted"}


# Bulk import (simplified - would use background task in production)
@router.post("/bulk/import")
async def bulk_import_candidates(
    candidates_data: List[CandidateCreate],
    db: Session = Depends(get_db)
):
    """Bulk import candidates"""
    count = 0
    for data in candidates_data:
        db_candidate = Candidate(
            name=data.name,
            email=data.email,
            phone=data.phone,
            location=data.location,
            education=json.dumps([e.model_dump() for e in data.education]) if data.education else None,
            work_experience=json.dumps([w.model_dump() for w in data.work_experience]) if data.work_experience else None,
            skills=json.dumps(data.skills) if data.skills else None,
            salary_expectation=json.dumps(data.salary_expectation) if data.salary_expectation else None,
            availability=data.availability,
            resume_text=data.resume_text,
        )
        db.add(db_candidate)
        count += 1
    
    db.commit()
    return {"imported": count}