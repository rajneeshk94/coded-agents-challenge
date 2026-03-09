from typing import TypedDict, List, Optional
from models import CandidateDetails, EligibilityResult


class AgentState(TypedDict):

    candidate_input: str

    candidate: Optional[CandidateDetails]

    result: Optional[EligibilityResult]

    skill_gap: Optional[List[str]]