from pydantic import BaseModel
from typing import Optional, Dict

class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0

class ChatResponse(BaseModel):
    answer: str
    usage: Usage
