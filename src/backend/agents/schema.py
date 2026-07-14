from pydantic import BaseModel
from typing import Dict, Optional, Any

class GraphState(BaseModel):
    user_input: str
    image_base64: Optional[str] = None
    parsed_query: Optional[Dict[str, Any]] = None
    profile: Optional[Dict[str, Any]] = None
    calculated_nutrition: Optional[Dict[str, Any]] = None
    recommendations: Optional[str] = None
