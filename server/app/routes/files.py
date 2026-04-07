"""File upload routes"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import os
import uuid
import aiofiles

from app.models import get_db, Candidate
from app.schemas import FileUploadResponse
from app.config import settings
from app.services.parser import parse_resume

router = APIRouter()


@router.post("/resume", response_model=FileUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a candidate resume (PDF/DOCX)"""
    # Validate file type
    allowed_types = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    if file.content_type not in allowed_types:
        return {"error": "Only PDF and DOCX files are allowed"}
    
    # Create upload directory
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(settings.upload_dir, unique_filename)
    
    # Save file
    content = await file.read()
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)
    
    # Return response
    return {
        "filename": file.filename,
        "file_path": file_path,
        "size": len(content),
        "content_type": file.content_type
    }


@router.post("/parse")
async def parse_resume_file(
    file: UploadFile = File(...),
):
    """Parse a resume file and return structured data"""
    # Validate file type
    allowed_types = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed")
    
    # Create temp file
    os.makedirs(settings.upload_dir, exist_ok=True)
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(settings.upload_dir, unique_filename)
    
    # Save and parse
    content = await file.read()
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)
    
    try:
        parsed = parse_resume(file_path)
        # Clean up temp file
        os.remove(file_path)
        return {"success": True, "data": parsed}
    except Exception as e:
        # Clean up temp file
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {str(e)}")


@router.post("/parse-resume")
async def parse_resume_text(
    candidate_id: int,
    resume_text: str,
    db: Session = Depends(get_db)
):
    """Parse resume text and update candidate"""
    from app.services.parser import parse_resume_text as parse_text
    
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Parse the text
    parsed = parse_text(resume_text)
    
    # Update candidate fields
    if parsed.get("name"):
        candidate.name = parsed["name"]
    if parsed.get("email"):
        candidate.email = parsed["email"]
    if parsed.get("phone"):
        candidate.phone = parsed["phone"]
    if parsed.get("location"):
        candidate.location = parsed["location"]
    
    # Store parsed data as JSON
    import json
    if parsed.get("skills"):
        candidate.skills = json.dumps(parsed["skills"])
    if parsed.get("work_experience"):
        candidate.work_experience = json.dumps(parsed["work_experience"])
    if parsed.get("education"):
        candidate.education = json.dumps(parsed["education"])
    if parsed.get("resume_text"):
        candidate.resume_text = parsed["resume_text"]
    
    # Calculate experience years if not found
    if not candidate.experience_years and parsed.get("experience_years"):
        candidate.experience_years = parsed["experience_years"]
    
    db.commit()
    
    return {
        "success": True,
        "message": "Resume parsed and candidate updated",
        "candidate_id": candidate_id,
        "parsed_fields": {
            "name": parsed.get("name"),
            "email": parsed.get("email"),
            "phone": parsed.get("phone"),
            "skills_count": len(parsed.get("skills", {}).get("hard_skills", [])),
            "experience_count": len(parsed.get("work_experience", [])),
            "education_count": len(parsed.get("education", [])),
        }
    }