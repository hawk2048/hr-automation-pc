"""Request/Response Schemas"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Any
from datetime import datetime


# ========== Job Schemas ==========

class Qualification(BaseModel):
    min_education: Optional[str] = None
    preferred_education: Optional[str] = None
    experience_years_min: Optional[int] = None
    experience_years_preferred: Optional[int] = None
    certificates: List[str] = []


class SkillRequirement(BaseModel):
    skill_id: Optional[str] = None
    name: str
    level: str = "熟练"  # 了解/熟练/精通
    weight: float = 0.2


class JobCreate(BaseModel):
    title: str
    department: Optional[str] = None
    description: Optional[str] = None
    
    qualifications: Optional[Qualification] = None
    skills: Optional[dict] = None  # {hard_skills: [], soft_skills: []}
    competencies: List[str] = []
    responsibilities: List[str] = []
    environment: Optional[dict] = None
    weights: Optional[dict] = None


class JobUpdate(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class JobResponse(BaseModel):
    id: int
    title: str
    department: Optional[str]
    description: Optional[str]
    qualifications: Optional[dict]
    skills: Optional[dict]
    competencies: List[str]
    responsibilities: List[str]
    environment: Optional[dict]
    weights: Optional[dict]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== Candidate Schemas ==========

class Education(BaseModel):
    degree: str
    major: str
    school: str
    year: Optional[int] = None


class WorkExperience(BaseModel):
    company: str
    industry: Optional[str] = None
    role: str
    duration_months: Optional[int] = None
    responsibilities: List[str] = []
    achievements: List[str] = []
    skills_used: List[str] = []


class CandidateCreate(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    
    education: List[Education] = []
    work_experience: List[WorkExperience] = []
    skills: Optional[dict] = None
    salary_expectation: Optional[dict] = None
    availability: Optional[str] = None
    resume_text: Optional[str] = None
    experience_years: Optional[int] = None


class CandidateUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None


class CandidateResponse(BaseModel):
    id: int
    name: str
    email: Optional[str]
    phone: Optional[str]
    location: Optional[str]
    education: List[dict]
    work_experience: List[dict]
    skills: Optional[dict]
    salary_expectation: Optional[dict]
    availability: Optional[str]
    experience_years: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== Match Schemas ==========

class MatchResultResponse(BaseModel):
    id: int
    job_id: int
    candidate_id: int
    total_score: float
    skill_score: float
    experience_score: float
    semantic_score: float
    education_score: float
    salary_score: float
    soft_skill_score: float
    llm_analysis: Optional[str]
    status: str
    created_at: datetime
    
    # Joined data
    candidate_name: Optional[str] = None
    candidate_location: Optional[str] = None
    
    class Config:
        from_attributes = True


class MatchResultUpdate(BaseModel):
    status: str  # reviewed, accepted, rejected


# ========== Auth Schemas ==========

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: str = "hr"


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    full_name: Optional[str]
    role: str

    class Config:
        from_attributes = True


# ========== File Upload ==========

class FileUploadResponse(BaseModel):
    filename: str
    file_path: str
    size: int
    content_type: Optional[str]