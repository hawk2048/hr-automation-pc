"""Matching service - Core AI matching logic"""
import json
import re
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models import Job, Candidate, MatchResult
from app.services.embedding import get_embedding_service


# Default weights (can be customized per job)
DEFAULT_WEIGHTS = {
    "skill": 0.30,
    "experience": 0.25,
    "semantic": 0.20,
    "education": 0.10,
    "salary": 0.10,
    "soft_skill": 0.05,
}


def normalize_skill_name(skill: str) -> str:
    """Normalize skill name for comparison"""
    # Remove common variations
    skill = skill.lower().strip()
    skill = re.sub(r'[.#\-+]', '', skill)
    
    # Common synonyms mapping
    synonyms = {
        "reactjs": "react",
        "react.js": "react",
        "typescript": "ts",
        "javascript": "js",
        "python": "py",
        "machine learning": "ml",
        "artificial intelligence": "ai",
        "sql": "database",
        "mysql": "database",
        "postgresql": "database",
    }
    return synonyms.get(skill, skill)


def calculate_skill_match(job_skills: dict, candidate_skills: dict) -> dict:
    """Calculate skill matching score"""
    if not job_skills or not candidate_skills:
        return {"score": 0.0, "matched": [], "missing": []}
    
    job_hard = set(normalize_skill_name(s.get("name", "")) for s in job_skills.get("hard_skills", []))
    cand_hard = set(normalize_skill_name(s.get("name", "")) for s in candidate_skills.get("hard_skills", []))
    
    matched = list(job_hard & cand_hard)
    missing = list(job_hard - cand_hard)
    
    if not job_hard:
        return {"score": 1.0, "matched": matched, "missing": missing}
    
    score = len(matched) / len(job_hard)
    
    # Weighted by importance
    weight_total = sum(s.get("weight", 0.2) for s in job_skills.get("hard_skills", []))
    if weight_total > 0:
        matched_weight = sum(
            s.get("weight", 0.2) 
            for s in job_skills.get("hard_skills", []) 
            if normalize_skill_name(s.get("name", "")) in matched
        )
        score = matched_weight / weight_total if weight_total > 0 else 0
    
    return {
        "score": round(score, 3), 
        "matched": matched, 
        "missing": missing
    }


def calculate_experience_match(job_qualifications: dict, candidate_experience: List[dict]) -> dict:
    """Calculate experience matching score"""
    min_years = job_qualifications.get("experience_years_min", 0) if job_qualifications else 0
    preferred_years = job_qualifications.get("experience_years_preferred") if job_qualifications else None
    
    if not candidate_experience:
        return {"score": 0.0, "total_years": 0}
    
    # Calculate total years of experience
    total_years = sum(exp.get("duration_months", 0) for exp in candidate_experience) / 12
    
    if min_years == 0:
        score = 1.0
    elif total_years >= (preferred_years or min_years + 2):
        score = 1.0
    elif total_years >= min_years:
        score = 0.7
    else:
        score = total_years / min_years if min_years > 0 else 0
    
    # Bonus for relevant industry experience
    # (simplified - could be enhanced)
    
    return {
        "score": round(score, 3),
        "total_years": round(total_years, 1)
    }


def calculate_education_match(job_qualifications: dict, candidate_education: List[dict]) -> dict:
    """Calculate education matching score"""
    min_edu = job_qualifications.get("min_education") if job_qualifications else None
    
    if not min_edu or not candidate_education:
        return {"score": 1.0 if not min_edu else 0.0, "match": None}
    
    edu_levels = {"高中": 1, "中专": 2, "大专": 3, "本科": 4, "硕士": 5, "博士": 6}
    
    min_level = edu_levels.get(min_edu, 4)  # default to 本科
    
    highest_edu = candidate_education[0] if candidate_education else {}
    highest_level = edu_levels.get(highest_edu.get("degree", ""), 0)
    
    if highest_level >= min_level:
        score = 1.0
    elif highest_level >= min_level - 1:
        score = 0.7
    else:
        score = 0.3
    
    return {
        "score": score,
        "match": highest_edu.get("degree") if candidate_education else None
    }


def calculate_salary_match(job_salary: Optional[dict], candidate_salary: Optional[dict]) -> dict:
    """Calculate salary matching score"""
    if not candidate_salary or not job_salary:
        return {"score": 1.0}  # neutral if not specified
    
    cand_min = candidate_salary.get("min", 0)
    cand_max = candidate_salary.get("max", 999999)
    job_min = job_salary.get("min", 0)
    job_max = job_salary.get("max", 999999)
    
    # Check overlap
    if cand_max < job_min:
        score = 0.3  # candidate expects less than job offers
    elif cand_min > job_max:
        score = 0.3  # candidate expects more than job offers
    else:
        score = 1.0  # overlap
    
    return {"score": score}


def calculate_soft_skill_match(job_soft: List[str], candidate_soft: List[dict]) -> dict:
    """Calculate soft skill matching (simplified)"""
    if not job_soft:
        return {"score": 1.0}
    
    cand_soft = set(normalize_skill_name(s.get("name", "")) for s in candidate_soft)
    matched = [s for s in job_soft if normalize_skill_name(s) in cand_soft]
    
    score = len(matched) / len(job_soft) if job_soft else 1.0
    
    return {"score": round(score, 3), "matched": matched}


def calculate_match(job: Job, candidate: Candidate, weights: Optional[dict] = None, embedding_service=None) -> dict:
    """Calculate overall match score"""
    w = weights or DEFAULT_WEIGHTS
    
    # Parse JSON fields
    job_qual = json.loads(job.qualifications) if job.qualifications else {}
    job_skills = json.loads(job.skills) if job.skills else {}
    cand_skills = json.loads(candidate.skills) if candidate.skills else {}
    cand_exp = json.loads(candidate.work_experience) if candidate.work_experience else []
    cand_edu = json.loads(candidate.education) if candidate.education else []
    job_env = json.loads(job.environment) if job.environment else {}
    
    # Calculate individual scores
    skill_result = calculate_skill_match(job_skills, cand_skills)
    exp_result = calculate_experience_match(job_qual, cand_exp)
    edu_result = calculate_education_match(job_qual, cand_edu)
    salary_result = calculate_salary_match(job_env.get("salary_range"), candidate.salary_expectation)
    soft_result = calculate_soft_skill_match(
        job_skills.get("soft_skills", []),
        cand_skills.get("soft_skills", [])
    )
    
    # Semantic score using BGE embeddings
    semantic_score = 0.5
    if embedding_service and job.description and candidate.resume_text:
        try:
            job_data = {
                "title": job.title or "",
                "description": job.description or "",
                "skills": job_skills,
                "qualifications": job_qual,
            }
            candidate_data = {
                "name": candidate.name or "",
                "resume_text": candidate.resume_text or "",
                "skills": cand_skills,
                "work_experience": cand_exp,
                "education": cand_edu,
            }
            
            job_emb = embedding_service.encode_job(job_data)
            cand_emb = embedding_service.encode_candidate(candidate_data)
            semantic_score = embedding_service.similarity(job_emb, cand_emb)
        except Exception:
            # Fallback to word overlap if embedding fails
            semantic_score = 0.5
    
    # Fallback: word overlap if no embedding service
    if semantic_score == 0.5 and job.description and candidate.resume_text:
        job_words = set(job.description.lower().split())
        cand_words = set(candidate.resume_text.lower().split())
        overlap = len(job_words & cand_words)
        total = len(job_words | cand_words)
        semantic_score = overlap / total if total > 0 else 0
    
    # Weighted total
    total = (
        skill_result["score"] * w.get("skill", 0.3) +
        exp_result["score"] * w.get("experience", 0.25) +
        semantic_score * w.get("semantic", 0.2) +
        edu_result["score"] * w.get("education", 0.1) +
        salary_result["score"] * w.get("salary", 0.1) +
        soft_result["score"] * w.get("soft_skill", 0.05)
    )
    
    return {
        "total_score": round(total, 3),
        "skill_score": skill_result["score"],
        "experience_score": exp_result["score"],
        "semantic_score": round(semantic_score, 3),
        "education_score": edu_result["score"],
        "salary_score": salary_result["score"],
        "soft_skill_score": soft_result["score"],
        "details": {
            "skill": skill_result,
            "experience": exp_result,
            "education": edu_result,
            "salary": salary_result,
            "soft_skill": soft_result,
        }
    }


async def match_job_to_candidates(
    db: Session, 
    job_id: int, 
    candidate_ids: Optional[List[int]] = None,
    top_n: int = 20,
    use_embeddings: bool = True
) -> List[MatchResult]:
    """Match a job to all candidates and return top matches"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return []
    
    # Get job weights
    job_weights = json.loads(job.weights) if job.weights else DEFAULT_WEIGHTS
    
    # Initialize embedding service if enabled
    embedding_service = None
    if use_embeddings:
        try:
            embedding_service = get_embedding_service()
        except Exception:
            # Silently fall back if embedding service unavailable
            pass
    
    # Get candidates
    if candidate_ids:
        candidates = db.query(Candidate).filter(Candidate.id.in_(candidate_ids)).all()
    else:
        candidates = db.query(Candidate).filter(Candidate.status != "rejected").all()
    
    results = []
    for candidate in candidates:
        # Check qualifications first (hard filter)
        job_qual = json.loads(job.qualifications) if job.qualifications else {}
        min_edu = job_qual.get("min_education")
        
        if min_edu:
            cand_edu = json.loads(candidate.education) if candidate.education else []
            edu_levels = {"高中": 1, "中专": 2, "大专": 3, "本科": 4, "硕士": 5, "博士": 6}
            min_level = edu_levels.get(min_edu, 4)
            highest_level = edu_levels.get(cand_edu[0].get("degree", "") if cand_edu else "", 0)
            if highest_level < min_level - 1:  # Allow one level difference
                continue  # Skip this candidate
        
        # Calculate score with optional embeddings
        scores = calculate_match(job, candidate, job_weights, embedding_service)
        
        # Save/update result
        existing = db.query(MatchResult).filter(
            MatchResult.job_id == job_id,
            MatchResult.candidate_id == candidate.id
        ).first()
        
        if existing:
            existing.total_score = scores["total_score"]
            existing.skill_score = scores["skill_score"]
            existing.experience_score = scores["experience_score"]
            existing.semantic_score = scores["semantic_score"]
            existing.education_score = scores["education_score"]
            existing.salary_score = scores["salary_score"]
            existing.soft_skill_score = scores["soft_skill_score"]
            result = existing
        else:
            result = MatchResult(
                job_id=job_id,
                candidate_id=candidate.id,
                total_score=scores["total_score"],
                skill_score=scores["skill_score"],
                experience_score=scores["experience_score"],
                semantic_score=scores["semantic_score"],
                education_score=scores["education_score"],
                salary_score=scores["salary_score"],
                soft_skill_score=scores["soft_skill_score"],
            )
            db.add(result)
        
        results.append(result)
    
    db.commit()
    
    # Reload results with scores
    results = db.query(MatchResult).filter(
        MatchResult.job_id == job_id
    ).order_by(MatchResult.total_score.desc()).limit(top_n).all()
    
    return results