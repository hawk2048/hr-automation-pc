"""Screening service - Batch candidate screening logic"""
import json
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models import Job, Candidate, MatchResult
from app.services.matching import calculate_match, DEFAULT_WEIGHTS
from app.services.evaluation import evaluate_candidate_with_llm, generate_interview_questions


class ScreeningCriteria:
    """初筛条件"""
    def __init__(
        self,
        min_total_score: float = 0.5,
        min_skill_score: float = 0.4,
        min_experience_score: float = 0.3,
        min_education_score: float = 0.3,
        exclude_rejected: bool = True,
        use_llm_evaluation: bool = False,
    ):
        self.min_total_score = min_total_score
        self.min_skill_score = min_skill_score
        self.min_experience_score = min_experience_score
        self.min_education_score = min_education_score
        self.exclude_rejected = exclude_rejected
        self.use_llm_evaluation = use_llm_evaluation


class ScreeningResult:
    """单个候选人初筛结果"""
    def __init__(
        self,
        match_id: int,
        candidate_id: int,
        candidate_name: str,
        total_score: float,
        passed: bool,
        reasons: List[str],
        llm_evaluation: Optional[dict] = None,
        interview_questions: Optional[List[dict]] = None,
    ):
        self.match_id = match_id
        self.candidate_id = candidate_id
        self.candidate_name = candidate_name
        self.total_score = total_score
        self.passed = passed
        self.reasons = reasons
        self.llm_evaluation = llm_evaluation
        self.interview_questions = interview_questions


def check_screening_criteria(
    match: MatchResult,
    candidate: Candidate,
    criteria: ScreeningCriteria,
    job: Job,
    embedding_service=None,
) -> ScreeningResult:
    """检查候选人是否满足初筛条件"""
    
    reasons = []
    passed = True
    
    # Check total score
    if match.total_score < criteria.min_total_score:
        passed = False
        reasons.append(f"综合分数 {match.total_score:.1%} 低于最低要求 {criteria.min_total_score:.1%}")
    
    # Check individual scores
    if match.skill_score < criteria.min_skill_score:
        passed = False
        reasons.append(f"技能分数 {match.skill_score:.1%} 低于最低要求 {criteria.min_skill_score:.1%}")
    
    if match.experience_score < criteria.min_experience_score:
        passed = False
        reasons.append(f"经验分数 {match.experience_score:.1%} 低于最低要求 {criteria.min_experience_score:.1%}")
    
    if match.education_score < criteria.min_education_score:
        passed = False
        reasons.append(f"学历分数 {match.education_score:.1%} 低于最低要求 {criteria.min_education_score:.1%}")
    
    # Additional checks
    if not candidate.email and not candidate.phone:
        passed = False
        reasons.append("缺少联系方式")
    
    if candidate.status == "rejected":
        passed = False
        reasons.append("候选人已被拒绝")
    
    # Add positive reasons if passed
    if passed:
        if match.total_score >= 0.8:
            reasons.append("优秀匹配 - 综合分数≥80%")
        if match.skill_score >= 0.8:
            reasons.append("技能高度匹配")
        if match.semantic_score >= 0.8:
            reasons.append("语义匹配度高")
    
    return ScreeningResult(
        match_id=match.id,
        candidate_id=candidate.id,
        candidate_name=candidate.name,
        total_score=match.total_score,
        passed=passed,
        reasons=reasons,
    )


async def batch_screen_candidates(
    db: Session,
    job_id: int,
    criteria: Optional[ScreeningCriteria] = None,
    candidate_ids: Optional[List[int]] = None,
) -> List[ScreeningResult]:
    """批量筛选候选人"""
    
    if criteria is None:
        criteria = ScreeningCriteria()
    
    # Get job
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return []
    
    # Get match results
    query = db.query(MatchResult).filter(MatchResult.job_id == job_id)
    
    if candidate_ids:
        query = query.filter(MatchResult.candidate_id.in_(candidate_ids))
    
    matches = query.order_by(MatchResult.total_score.desc()).all()
    
    results = []
    for match in matches:
        candidate = db.query(Candidate).filter(Candidate.id == match.candidate_id).first()
        if not candidate:
            continue
        
        # Exclude rejected if requested
        if criteria.exclude_rejected and candidate.status == "rejected":
            continue
        
        result = check_screening_criteria(match, candidate, criteria, job)
        
        # LLM evaluation if enabled
        if criteria.use_llm_evaluation and result.passed:
            try:
                job_qual = json.loads(job.qualifications) if job.qualifications else {}
                job_skills = json.loads(job.skills) if job.skills else {}
                
                eval_result = await evaluate_candidate_with_llm(
                    job_title=job.title,
                    job_description=job.description or "",
                    job_requirements={
                        **job_qual,
                        "hard_skills": job_skills.get("hard_skills", []),
                        "soft_skills": job_skills.get("soft_skills", []),
                    },
                    candidate_info={
                        "name": candidate.name,
                        "email": candidate.email,
                        "phone": candidate.phone,
                    },
                    candidate_resume=candidate.resume_text or "",
                )
                
                if eval_result.get("success"):
                    result.llm_evaluation = eval_result["evaluation"]
                    
                    # Generate interview questions
                    questions_result = await generate_interview_questions(
                        job_title=job.title,
                        job_requirements=job_qual,
                        candidate_background=candidate.resume_text or "",
                        num_questions=5,
                    )
                    
                    if questions_result.get("success"):
                        result.interview_questions = questions_result["questions"]
                        
            except Exception:
                pass  # Continue even if LLM fails
        
        results.append(result)
    
    return results


async def batch_accept_candidates(
    db: Session,
    match_ids: List[int],
    target_status: str = "screening",
) -> dict:
    """批量通过候选人"""
    
    accepted = []
    failed = []
    
    for match_id in match_ids:
        match = db.query(MatchResult).filter(MatchResult.id == match_id).first()
        if not match:
            failed.append({"id": match_id, "reason": "Match not found"})
            continue
        
        # Update match status
        match.status = "accepted"
        
        # Update candidate status
        candidate = db.query(Candidate).filter(Candidate.id == match.candidate_id).first()
        if candidate:
            candidate.status = target_status
        
        accepted.append(match_id)
    
    db.commit()
    
    return {
        "accepted": accepted,
        "failed": failed,
        "total": len(accepted),
    }


async def batch_reject_candidates(
    db: Session,
    match_ids: List[int],
) -> dict:
    """批量拒绝候选人"""
    
    rejected = []
    failed = []
    
    for match_id in match_ids:
        match = db.query(MatchResult).filter(MatchResult.id == match_id).first()
        if not match:
            failed.append({"id": match_id, "reason": "Match not found"})
            continue
        
        # Update match status
        match.status = "rejected"
        
        # Update candidate status
        candidate = db.query(Candidate).filter(Candidate.id == match.candidate_id).first()
        if candidate:
            candidate.status = "rejected"
        
        rejected.append(match_id)
    
    db.commit()
    
    return {
        "rejected": rejected,
        "failed": failed,
        "total": len(rejected),
    }


def get_screening_stats(db: Session, job_id: int) -> dict:
    """获取岗位初筛统计"""
    
    matches = db.query(MatchResult).filter(MatchResult.job_id == job_id).all()
    
    total = len(matches)
    pending = sum(1 for m in matches if m.status == "pending")
    accepted = sum(1 for m in matches if m.status == "accepted")
    rejected = sum(1 for m in matches if m.status == "rejected")
    
    # Calculate pass rate
    scored = [m for m in matches if m.total_score > 0]
    excellent = sum(1 for m in scored if m.total_score >= 0.8)
    good = sum(1 for m in scored if m.total_score >= 0.6 and m.total_score < 0.8)
    fair = sum(1 for m in scored if m.total_score >= 0.4 and m.total_score < 0.6)
    poor = sum(1 for m in scored if m.total_score < 0.4)
    
    return {
        "total": total,
        "pending": pending,
        "accepted": accepted,
        "rejected": rejected,
        "excellent": excellent,  # ≥80%
        "good": good,           # 60-80%
        "fair": fair,           # 40-60%
        "poor": poor,           # <40%
        "pass_rate": round(accepted / total * 100, 1) if total > 0 else 0,
    }