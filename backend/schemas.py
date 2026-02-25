from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ToolResponse(BaseModel):
    tool_name: str
    model: str
    why_recommended: str
    key_specs: List[str]
    voltage: str
    ip_rating: str
    image_path: str
    confidence: str

class Query(BaseModel):
    question: str
    session_id: Optional[str] = None

class SessionState(BaseModel):
    session_id: str
    conversation_history: List[Dict[str, Any]]
    extracted_filters: Dict[str, Any]
    last_query: str
    clarification_count: int