"""Job routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.models import get_db, Job
from app.schemas import JobCreate, JobUpdate, JobResponse
from app.errors import NotFoundError

router = APIRouter()


def job_to_response(job: Job) -> JobResponse:
    """Convert Job model to schema"""
    return JobResponse(
        id=job.id,
        title=job.title,
        department=job.department,
        description=job.description,
        qualifications=job.qualifications,
        skills=job.skills,
        competencies=job.competencies or [],
        responsibilities=job.responsibilities or [],
        environment=job.environment,
        weights=job.weights,
        is_active=job.is_active,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.post("/", response_model=JobResponse)
async def create_job(job_data: JobCreate, db: Session = Depends(get_db)):
    """Create a new job"""
    db_job = Job(
        title=job_data.title,
        department=job_data.department,
        description=job_data.description,
        qualifications=job_data.qualifications.model_dump() if job_data.qualifications else None,
        skills=job_data.skills,
        competencies=job_data.competencies,
        responsibilities=job_data.responsibilities,
        environment=job_data.environment,
        weights=job_data.weights or {"base": 0.2, "core": 0.5, "potential": 0.3},
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return job_to_response(db_job)


@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """List all jobs"""
    query = db.query(Job)
    if active_only:
        query = query.filter(Job.is_active == True)
    jobs = query.order_by(Job.created_at.desc()).all()
    return [job_to_response(j) for j in jobs]


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get a job by ID"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise NotFoundError("Job", job_id)
    return job_to_response(job)


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int, 
    job_data: JobUpdate, 
    db: Session = Depends(get_db)
):
    """Update a job"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise NotFoundError("Job", job_id)
    
    if job_data.title is not None:
        job.title = job_data.title
    if job_data.department is not None:
        job.department = job_data.department
    if job_data.description is not None:
        job.description = job_data.description
    if job_data.is_active is not None:
        job.is_active = job_data.is_active
    
    db.commit()
    db.refresh(job)
    return job_to_response(job)


@router.delete("/{job_id}")
async def delete_job(job_id: int, db: Session = Depends(get_db)):
    """Delete a job (soft delete)"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise NotFoundError("Job", job_id)
    
    job.is_active = False
    db.commit()
    return {"message": "Job deleted"}


# Batch operations
@router.post("/batch/delete")
async def batch_delete_jobs(job_ids: List[int], db: Session = Depends(get_db)):
    """Batch delete jobs"""
    jobs = db.query(Job).filter(Job.id.in_(job_ids)).all()
    for job in jobs:
        job.is_active = False
    db.commit()
    return {"deleted": len(jobs)}