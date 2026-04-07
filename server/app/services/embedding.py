"""HR Automation - Embedding Service using BGE models"""
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from app.config import settings


class EmbeddingService:
    """BGE Embedding service for semantic search"""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.embedding_model
        self._model = None

    @property
    def model(self):
        """Lazy load model"""
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode(self, texts: str | List[str], normalize: bool = True) -> np.ndarray:
        """Encode texts to embeddings"""
        if isinstance(texts, str):
            texts = [texts]
        return self.model.encode(texts, normalize_embeddings=normalize)

    def encode_job(self, job_data: dict) -> np.ndarray:
        """Encode job posting for matching"""
        # Combine job title, description, skills, requirements
        parts = [
            job_data.get("title", ""),
            job_data.get("description", ""),
        ]
        
        skills = job_data.get("skills", {})
        if skills:
            hard_skills = [s.get("name", "") for s in skills.get("hard_skills", [])]
            parts.extend(hard_skills)
        
        qual = job_data.get("qualifications", {})
        if qual:
            parts.append(f"Experience: {qual.get('experience_years_min', 0)}+ years")
            if qual.get("min_education"):
                parts.append(f"Education: {qual.get('min_education')}")
        
        text = " ".join(parts)
        return self.encode(text)

    def encode_candidate(self, candidate_data: dict) -> np.ndarray:
        """Encode candidate profile for matching"""
        parts = [
            candidate_data.get("name", ""),
            candidate_data.get("resume_text", ""),
        ]
        
        skills = candidate_data.get("skills", {})
        if skills:
            hard_skills = [s.get("name", "") for s in skills.get("hard_skills", [])]
            parts.extend(hard_skills)
        
        experience = candidate_data.get("work_experience", [])
        if experience:
            # Summarize experience
            for exp in experience[:3]:  # Top 3 jobs
                parts.append(exp.get("title", ""))
                parts.append(exp.get("company", ""))
        
        education = candidate_data.get("education", [])
        if education:
            for edu in education:
                parts.append(edu.get("degree", ""))
                parts.append(edu.get("major", ""))
        
        text = " ".join(parts)
        return self.encode(text)

    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings"""
        return float(np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        ))

    def batch_similarity(
        self,
        query_embedding: np.ndarray,
        candidate_embeddings: List[np.ndarray]
    ) -> List[float]:
        """Calculate similarity between query and multiple candidates"""
        # Normalize for cosine similarity
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        cand_norm = candidate_embeddings / np.linalg.norm(
            candidate_embeddings, axis=1, keepdims=True
        )
        return np.dot(cand_norm, query_norm).tolist()


# Global instance
embedding_service = EmbeddingService()


def get_embedding_service(model_name: Optional[str] = None) -> EmbeddingService:
    """Factory function for embedding service"""
    if model_name:
        return EmbeddingService(model_name)
    return embedding_service