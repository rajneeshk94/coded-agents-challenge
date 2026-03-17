"""
Resume Reviewer Agent - UiPath Coded Agent Challenge
Uses LangGraph + UiPath SDK to review resumes for campus placements.
"""

import json
import os
from typing import Annotated, Any

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

# ── UiPath / LangChain wiring ────────────────────────────────────────────────
try:
    from uipath_langchain.chat import UiPathChatModel
    llm = UiPathChatModel(model="claude-sonnet-4-20250514")
except Exception:
    # Fallback: direct Anthropic key (set ANTHROPIC_API_KEY in .env)
    from langchain_anthropic import ChatAnthropic
    llm = ChatAnthropic(model="claude-sonnet-4-20250514")


# ── State definition ─────────────────────────────────────────────────────────
class ResumeState(TypedDict):
    # Inputs
    resume_text: str
    target_role: str
    # Intermediate
    messages: Annotated[list, add_messages]
    extraction: dict          # parsed resume sections
    skill_gaps: list[str]     # missing skills
    retry_count: int          # retry mechanism counter
    # Outputs
    score: int                # 0-100
    feedback: str
    recommendation: str       # "Strong Hire" | "Maybe" | "Reject"
    final_report: dict


# ── Node 1: Extract & Parse Resume ──────────────────────────────────────────
def extract_resume_info(state: ResumeState) -> dict:
    """Parse the raw resume text into structured sections."""
    print("[Node 1] Extracting resume information...")

    prompt = f"""You are a resume parser. Extract information from this resume and return ONLY valid JSON (no markdown, no extra text).

Resume:
{state['resume_text']}

Return this exact JSON structure:
{{
  "name": "candidate name or Unknown",
  "education": "degree and institution",
  "experience_years": 0,
  "skills": ["skill1", "skill2"],
  "projects": ["project1"],
  "certifications": ["cert1"],
  "summary": "one sentence about candidate"
}}"""

    response = llm.invoke([HumanMessage(content=prompt)])
    raw = response.content.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        extraction = json.loads(raw.strip())
    except json.JSONDecodeError:
        extraction = {
            "name": "Unknown",
            "education": "Not parsed",
            "experience_years": 0,
            "skills": [],
            "projects": [],
            "certifications": [],
            "summary": raw[:200],
        }

    return {
        "extraction": extraction,
        "messages": [HumanMessage(content=f"Extracted info: {json.dumps(extraction)}")],
        "retry_count": state.get("retry_count", 0),
    }


# ── Node 2: Skill Gap Analysis ───────────────────────────────────────────────
def analyze_skill_gaps(state: ResumeState) -> dict:
    """Compare candidate skills against target role requirements."""
    print("[Node 2] Analysing skill gaps...")

    role_requirements = {
        "software engineer": ["Python", "Data Structures", "System Design", "Git", "SQL"],
        "data scientist": ["Python", "Machine Learning", "Statistics", "SQL", "Pandas"],
        "product manager": ["Agile", "User Research", "Data Analysis", "Roadmapping", "Communication"],
        "devops engineer": ["Docker", "Kubernetes", "CI/CD", "Linux", "Cloud"],
        "frontend developer": ["React", "JavaScript", "CSS", "HTML", "TypeScript"],
    }

    target = state["target_role"].lower()
    required = role_requirements.get(target, ["Communication", "Problem Solving", "Teamwork"])
    candidate_skills = [s.lower() for s in state["extraction"].get("skills", [])]

    gaps = [req for req in required if req.lower() not in candidate_skills]

    return {
        "skill_gaps": gaps,
        "messages": [HumanMessage(content=f"Skill gaps identified: {gaps}")],
    }


# ── Node 3: Score & Evaluate ─────────────────────────────────────────────────
def score_resume(state: ResumeState) -> dict:
    """Use LLM to score the resume and generate detailed feedback."""
    print("[Node 3] Scoring resume...")

    extraction = state["extraction"]
    gaps = state["skill_gaps"]

    prompt = f"""You are an expert campus placement recruiter. Evaluate this candidate for the role of {state['target_role']}.

Candidate Profile:
{json.dumps(extraction, indent=2)}

Identified Skill Gaps: {gaps}

Return ONLY valid JSON (no markdown):
{{
  "score": <integer 0-100>,
  "strengths": ["strength1", "strength2"],
  "weaknesses": ["weakness1"],
  "feedback": "2-3 sentence actionable feedback",
  "recommendation": "Strong Hire" or "Maybe" or "Reject"
}}"""

    response = llm.invoke([HumanMessage(content=prompt)])
    raw = response.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        result = json.loads(raw.strip())
        score = int(result.get("score", 50))
        feedback = result.get("feedback", "No feedback generated.")
        recommendation = result.get("recommendation", "Maybe")
    except (json.JSONDecodeError, ValueError):
        score = 50
        feedback = "Unable to generate detailed feedback."
        recommendation = "Maybe"
        result = {}

    return {
        "score": score,
        "feedback": feedback,
        "recommendation": recommendation,
        "messages": [HumanMessage(content=f"Score: {score}, Recommendation: {recommendation}")],
    }


# ── Node 4: Self-Evaluation / Retry ─────────────────────────────────────────
def self_evaluate(state: ResumeState) -> dict:
    """Check if score seems reasonable; flag for retry if suspicious."""
    print("[Node 4] Self-evaluating result quality...")

    score = state.get("score", 0)
    extraction = state.get("extraction", {})
    retry_count = state.get("retry_count", 0)

    # If score is extreme (0 or 100) and skills list is non-empty, something may be wrong
    skills_count = len(extraction.get("skills", []))
    suspicious = (score in (0, 100)) and skills_count > 3 and retry_count < 2

    if suspicious:
        print(f"  ⚠  Suspicious score ({score}) — will retry scoring (attempt {retry_count + 1})")

    return {"retry_count": retry_count + (1 if suspicious else 0)}


# ── Node 5: Build Final Report ────────────────────────────────────────────────
def build_final_report(state: ResumeState) -> dict:
    """Assemble all outputs into a structured final report."""
    print("[Node 5] Building final report...")

    report = {
        "candidate_name": state["extraction"].get("name", "Unknown"),
        "target_role": state["target_role"],
        "overall_score": state["score"],
        "recommendation": state["recommendation"],
        "feedback": state["feedback"],
        "skill_gaps": state["skill_gaps"],
        "profile_summary": state["extraction"].get("summary", ""),
        "education": state["extraction"].get("education", ""),
        "experience_years": state["extraction"].get("experience_years", 0),
        "top_skills": state["extraction"].get("skills", []),
        "status": "completed",
    }

    print(f"\n{'='*50}")
    print(f"  FINAL REPORT: {report['candidate_name']}")
    print(f"  Score: {report['overall_score']}/100")
    print(f"  Recommendation: {report['recommendation']}")
    print(f"{'='*50}\n")

    return {"final_report": report}


# ── Conditional Routing ───────────────────────────────────────────────────────
def should_retry_scoring(state: ResumeState) -> str:
    """Route back to scoring if result looks suspicious, else finalize."""
    retry_count = state.get("retry_count", 0)
    score = state.get("score", 50)
    suspicious = (score in (0, 100)) and retry_count < 2 and retry_count > 0

    if suspicious:
        return "retry_score"
    return "finalize"


def route_by_recommendation(state: ResumeState) -> str:
    """Different final-report paths based on recommendation tier."""
    rec = state.get("recommendation", "Maybe")
    if rec == "Strong Hire":
        return "strong_hire_path"
    elif rec == "Reject":
        return "reject_path"
    return "maybe_path"


# ── Graph Construction ────────────────────────────────────────────────────────
def build_graph() -> StateGraph:
    graph = StateGraph(ResumeState)

    # Add nodes
    graph.add_node("extract", extract_resume_info)
    graph.add_node("skill_gap", analyze_skill_gaps)
    graph.add_node("score", score_resume)
    graph.add_node("self_eval", self_evaluate)
    graph.add_node("report", build_final_report)

    # Linear flow
    graph.add_edge(START, "extract")
    graph.add_edge("extract", "skill_gap")
    graph.add_edge("skill_gap", "score")
    graph.add_edge("score", "self_eval")

    # Conditional: retry scoring OR move to report
    graph.add_conditional_edges(
        "self_eval",
        should_retry_scoring,
        {
            "retry_score": "score",   # loop back
            "finalize": "report",
        },
    )

    graph.add_edge("report", END)

    return graph


# ── Compiled graph (UiPath entry point) ───────────────────────────────────────
graph = build_graph().compile()


# ── Local runner ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sample_input = {
        "resume_text": """
        John Doe | john.doe@email.com | github.com/johndoe

        EDUCATION
        B.Tech Computer Science, IIT Delhi (2021-2025) | CGPA: 8.4/10

        SKILLS
        Python, JavaScript, React, SQL, Git, Docker, Machine Learning basics

        PROJECTS
        - E-Commerce Platform: Built full-stack app using React and Node.js with 500+ users
        - ML Price Predictor: Trained regression model achieving 92% accuracy on housing data

        EXPERIENCE
        Software Intern, TechCorp (May 2024 - Jul 2024)
        - Developed REST APIs reducing response time by 30%
        - Collaborated in Agile team of 8 engineers

        CERTIFICATIONS
        AWS Cloud Practitioner, Coursera ML Specialization
        """,
        "target_role": "Software Engineer",
        "messages": [],
        "extraction": {},
        "skill_gaps": [],
        "retry_count": 0,
        "score": 0,
        "feedback": "",
        "recommendation": "",
        "final_report": {},
    }

    result = graph.invoke(sample_input)
    print(json.dumps(result["final_report"], indent=2))
