from typing import TypedDict, List

class StyleState(TypedDict):
    event: str
    weather: str
    wardrobe: List[str]

    tops: List[str]
    bottoms: List[str]

    context: str
    outfit: str
    alternatives: List[str]

    explanation: str
    confidence: float