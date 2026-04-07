"""HR Automation - LLM Candidate Evaluation Service"""
import json
from typing import Optional
from app.services.llm import get_llm_service


async def evaluate_candidate_with_llm(
    job_title: str,
    job_description: str,
    job_requirements: dict,
    candidate_info: dict,
    candidate_resume: str,
) -> dict:
    """Use LLM to deeply evaluate candidate fit for a job"""
    
    llm = get_llm_service()
    
    # Build prompt for candidate evaluation
    system_prompt = """You are an expert HR recruiter and technical interviewer. 
Your task is to evaluate how well a candidate matches a job position.
Provide a detailed assessment covering:
1. Technical skills match (0-100)
2. Experience relevance (0-100)  
3. Education fit (0-100)
4. Cultural fit potential (0-100)
5. Overall recommendation (STRONG_YES / YES / MAYBE / NO)
6. Key strengths (list 3-5)
7. Concerns/risk factors (list 2-4)
8. Suggested interview focus areas

Be honest and objective. If there are red flags, mention them clearly."""

    prompt = f"""Job Position: {job_title}

Job Description:
{job_description}

Job Requirements:
- Min Experience: {job_requirements.get('experience_years_min', 'Not specified')} years
- Preferred Experience: {job_requirements.get('experience_years_preferred', 'Not specified')} years
- Min Education: {job_requirements.get('min_education', 'Not specified')}
- Required Skills: {', '.join([s.get('name', '') for s in job_requirements.get('hard_skills', [])])}
- Preferred Skills: {', '.join([s.get('name', '') for s in job_requirements.get('soft_skills', [])])}

Candidate Name: {candidate_info.get('name', 'Unknown')}
Candidate Resume:
{candidate_resume}

Please provide a detailed evaluation in JSON format:
```json
{{
  "technical_score": <0-100>,
  "experience_score": <0-100>,
  "education_score": <0-100>,
  "cultural_fit_score": <0-100>,
  "overall_recommendation": "STRONG_YES|YES|MAYBE|NO",
  "strengths": ["...", "...", "..."],
  "concerns": ["...", "..."],
  "interview_focus": ["...", "..."],
  "summary": "Brief 2-3 sentence summary"
}}
```"""

    try:
        response = await llm.generate(
            prompt=prompt,
            system=system_prompt,
            temperature=0.3,
            max_tokens=1500,
        )
        
        # Parse JSON from response
        # Find JSON block in response
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = response[json_start:json_end]
            evaluation = json.loads(json_str)
            return {
                "success": True,
                "evaluation": evaluation,
                "raw_response": response,
            }
        else:
            # If no JSON found, return raw response
            return {
                "success": False,
                "error": "Failed to parse LLM response",
                "raw_response": response,
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "raw_response": None,
        }


async def generate_interview_questions(
    job_title: str,
    job_requirements: dict,
    candidate_background: str,
    num_questions: int = 5,
) -> dict:
    """Generate tailored interview questions based on job and candidate"""
    
    llm = get_llm_service()
    
    system_prompt = """You are an expert technical interviewer. 
Generate insightful interview questions that assess candidates specifically for the role.
Create behavioral and technical questions based on the candidate's background."""

    prompt = f"""Job Title: {job_title}
Job Requirements: {json.dumps(job_requirements)}

Candidate Background:
{candidate_background}

Generate {num_questions} interview questions. For each question, specify:
- Type: technical/behavioral/problem-solving
- Purpose: what it assesses
- Follow-up: suggested follow-up question

Return as JSON:
```json
{{
  "questions": [
    {{
      "type": "...",
      "question": "...",
      "purpose": "...",
      "follow_up": "..."
    }},
    ...
  ]
}}
```"""

    try:
        response = await llm.generate(
            prompt=prompt,
            system=system_prompt,
            temperature=0.7,
            max_tokens=1000,
        )
        
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = response[json_start:json_end]
            questions = json.loads(json_str)
            return {"success": True, "questions": questions.get("questions", [])}
        else:
            return {"success": False, "error": "Failed to parse response"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


async def generate_candidate_summary(
    candidate_info: dict,
    resume_text: str,
    match_results: list,
) -> str:
    """Generate a concise summary of candidate using LLM"""
    
    llm = get_llm_service()
    
    prompt = f"""Candidate: {candidate_info.get('name', 'Unknown')}
Email: {candidate_info.get('email', 'Not provided')}
Phone: {candidate_info.get('phone', 'Not provided')}

Resume:
{resume_text[:2000]}

Match Scores (if available):
{match_results[:5]}

Provide a brief 3-4 sentence professional summary of this candidate highlighting their key strengths and experience."""

    try:
        summary = await llm.generate(
            prompt=prompt,
            system="You are an HR professional writing candidate summaries.",
            temperature=0.5,
            max_tokens=300,
        )
        return summary.strip()
    except Exception:
        return f"{candidate_info.get('name', 'Candidate')}: {resume_text[:200]}..."