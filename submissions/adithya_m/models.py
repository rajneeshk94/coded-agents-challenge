from pydantic import BaseModel
from typing import List, Optional


class CandidateDetails(BaseModel):

    name: str = ""
    gpa: float = 0
    graduation_year: int = 0
    skills: List[str] = []


class EligibilityResult(BaseModel):

    is_eligible: bool
    reasons: List[str]
    suggested_role: Optional[str]
    next_steps: str