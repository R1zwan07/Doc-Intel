from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

# ===== EXISTING RESPONSE MODEL =====
class AnalysisResponse(BaseModel):
    file_id: str
    filename: str
    extracted_text: Optional[str] = None
    summary: str
    key_points: List[str]
    diagram_code: str
    processed_at: datetime


# ===== DIAGRAM MODEL =====
class Diagram(BaseModel):
    title: str
    type: str
    code: str
    description: Optional[str] = None


# ===== Q&A MODELS =====
class QuestionRequest(BaseModel):
    question: str


class QuestionResponse(BaseModel):
    question: str
    answer: str
    contexts: Optional[List[Dict]] = []
    chunks_used: int = 0
    error: Optional[str] = None


# ===== RAG STATUS =====
class RAGStatus(BaseModel):
    is_indexed: bool
    doc_id: Optional[str] = None
    chunks_count: Optional[int] = None