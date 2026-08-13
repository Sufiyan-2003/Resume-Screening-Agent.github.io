from pydantic import BaseModel
from typing import Any

class HealthResponse(BaseModel):
    status: str
class CandidateResponse(BaseModel):
    id: int | None = None
    name: str
    score: float
    rank: int
    recommendation: str
    class Config: extra = "allow"
class RunResponse(BaseModel):
    id: int
    job_title: str
    total_candidates: int
    candidates: list[CandidateResponse]
    class Config: extra = "allow"
