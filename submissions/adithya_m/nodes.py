from langchain_core.messages import HumanMessage
from state import AgentState
from models import CandidateDetails, EligibilityResult
import datetime
import re
from langchain_core.messages import HumanMessage


def responder(state):

    state.candidate = candidate_info
    result = state["result"]
    skill_gap = state.get("skill_gap", [])

    response = f"""
Eligibility Check for {candidate.name}

Status: {"Eligible" if result.is_eligible else "Not Eligible"}

Reasons:
{chr(10).join("- " + r for r in result.reasons)}

Skill Gap:
{", ".join(skill_gap) if skill_gap else "None"}

Suggested Role:
{result.suggested_role}
"""

    return {"messages": [HumanMessage(content=response)]}


def extractor(state):

    text = state["candidate_input"].lower()

    name = state["candidate_input"].split(",")[0].strip()

    skills = []

    if "python" in text:
        skills.append("Python")

    if "react" in text:
        skills.append("React")

    if "sql" in text:
        skills.append("SQL")

    candidate = CandidateDetails(
        name=name,
        gpa=8.5,
        graduation_year=2026,
        skills=skills
    )

    return {"candidate": candidate}

def eligibility_checker(state):

    candidate = state["candidate"]

    eligible = candidate.gpa >= 7.0

    result = EligibilityResult(
        is_eligible=eligible,
        reasons=["Candidate meets requirements"] if eligible else ["GPA too low"],
        suggested_role="Software Engineering Intern" if eligible else None,
        next_steps="Prepare for technical interview"
    )

    return {"result": result}


def responder(state):

    candidate = state["candidate"]
    result = state["result"]
    skill_gap = state.get("skill_gap", [])

    response = f"""
Eligibility Check for {candidate.name}

Status: {"Eligible" if result.is_eligible else "Not Eligible"}

Reasons:
{chr(10).join("- " + r for r in result.reasons)}

Skill Gap:
{", ".join(skill_gap) if skill_gap else "None"}

Suggested Role:
{result.suggested_role}
"""

    return {"messages": [HumanMessage(content=response)]}

def skill_gap_analyzer(state):

    candidate = state["candidate"]

    required = [
        "Python",
        "Data Structures",
        "Algorithms",
        "Git",
        "System Design"
    ]

    candidate_skills = [s.lower() for s in candidate.skills]

    missing = []

    for skill in required:
        if skill.lower() not in candidate_skills:
            missing.append(skill)

    return {"skill_gap": missing}
