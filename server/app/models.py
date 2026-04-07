"""Database models and connection"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Mapped, mapped_column
from sqlalchemy import String, Integer, Text, Float, Boolean, DateTime, JSON
from datetime import datetime
from typing import Optional

from app.config import settings

# Create engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=False,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class
Base = declarative_base()


def get_db():
    """Dependency for getting DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


# ========== Models ==========

class Job(Base):
    """岗位画像"""
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # JSON fields for structured data
    qualifications: Mapped[Optional[str]] = mapped_column(JSON)  # dict
    skills: Mapped[Optional[str]] = mapped_column(JSON)  # hard_skills, soft_skills
    competencies: Mapped[Optional[str]] = mapped_column(JSON)  # list of competency ids
    responsibilities: Mapped[Optional[str]] = mapped_column(JSON)  # list
    environment: Mapped[Optional[str]] = mapped_column(JSON)  # dict
    
    # Weights
    weights: Mapped[Optional[str]] = mapped_column(JSON)  # {"base": 0.2, "core": 0.5, "potential": 0.3}
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Candidate(Base):
    """人才画像"""
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Basic info
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    location: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Education
    education: Mapped[Optional[str]] = mapped_column(JSON)  # list of education records
    
    # Work experience
    work_experience: Mapped[Optional[str]] = mapped_column(JSON)  # list of work records
    
    # Skills
    skills: Mapped[Optional[str]] = mapped_column(JSON)  # hard_skills, soft_skills
    
    # Other
    salary_expectation: Mapped[Optional[str]] = mapped_column(JSON)  # {min, max}
    availability: Mapped[Optional[str]] = mapped_column(String(50))
    resume_text: Mapped[Optional[str]] = mapped_column(Text)  # raw resume text for embedding
    resume_file: Mapped[Optional[str]] = mapped_column(String(500))  # file path
    
    # Experience
    experience_years: Mapped[Optional[int]] = mapped_column(Integer)  # years of experience
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="new")  # new, screening, interview, offer, hired, rejected


class User(Base):
    """系统用户 (HR)"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(200))
    hashed_password: Mapped[str] = mapped_column(String(200))
    full_name: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Role
    role: Mapped[str] = mapped_column(String(50), default="hr")  # admin, hr, recruiter
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MatchResult(Base):
    """匹配结果"""
    __tablename__ = "match_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(Integer, nullable=False)
    candidate_id: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Scores
    total_score: Mapped[float] = mapped_column(Float)
    skill_score: Mapped[float] = mapped_column(Float)
    experience_score: Mapped[float] = mapped_column(Float)
    semantic_score: Mapped[float] = mapped_column(Float)
    education_score: Mapped[float] = mapped_column(Float)
    salary_score: Mapped[float] = mapped_column(Float)
    soft_skill_score: Mapped[float] = mapped_column(Float)
    
    # LLM analysis (optional)
    llm_analysis: Mapped[Optional[str]] = mapped_column(Text)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, reviewed, accepted, rejected
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)