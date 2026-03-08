from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt
from langchain_core.messages import HumanMessage
from uipath_langchain.chat.models import UiPathAzureChatOpenAI
from uipath.platform.common import CreateTask
import json, re


# ===== LLM Setup =====

llm = UiPathAzureChatOpenAI(
    model="gpt-4o-2024-08-06",
    temperature=0,
    max_tokens=2000,
    timeout=30,
    max_retries=2
)


# ===== Graph State =====

class GraphState(BaseModel):

    student_profile: str
    internship_role: str

    extracted_skills: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)

    eligible: bool | None = None
    skill_gap: list[str] = Field(default_factory=list)

    improvement_plan: str | None = None
    evaluation_confidence: float | None = None


# ===== Helper Function =====

def parse_json(response):

    match = re.search(r"\{.*\}", response, re.S)

    if match:
        return json.loads(match.group(0))

    return {}


# ===== Node 1 — Extract Student Skills =====

def extract_student_skills(state: GraphState):

    prompt = f"""
    Extract technical skills from the student profile.

    Return JSON:
    {{
        "skills":[]
    }}

    Profile:
        {state.student_profile}
    """

    response = llm.invoke([HumanMessage(content=prompt)]).content

    result = parse_json(response)

    skills = result.get("skills", [])

    return GraphState(
        student_profile=state.student_profile,
        internship_role=state.internship_role,
        extracted_skills=skills
    )


# ===== Node 2 — Extract Role Skills =====

def extract_required_skills(state: GraphState):

    prompt = f"""
Identify required skills for this internship role.

Return JSON:
{{
 "required_skills":[]
}}

Role:
{state.internship_role}
"""

    response = llm.invoke([HumanMessage(content=prompt)]).content

    result = parse_json(response)

    required = result.get("required_skills", [])

    return GraphState(
        student_profile=state.student_profile,
        internship_role=state.internship_role,
        extracted_skills=state.extracted_skills,
        required_skills=required
    )


# ===== Node 3 — Evaluate Eligibility =====

def evaluate_eligibility(state: GraphState):

    student = set(s.lower() for s in state.extracted_skills)
    required = set(s.lower() for s in state.required_skills)

    gap = list(required - student)

    eligible = len(gap) <= 2

    confidence = max(0.5, 1 - (len(gap) * 0.15))

    return GraphState(
        student_profile=state.student_profile,
        internship_role=state.internship_role,
        extracted_skills=state.extracted_skills,
        required_skills=state.required_skills,
        eligible=eligible,
        skill_gap=gap,
        evaluation_confidence=confidence
    )


# ===== Node 4 — Self Evaluation =====

def self_evaluate(state: GraphState):

    prompt = f"""
Evaluate whether the eligibility decision is reasonable.

Student skills: {state.extracted_skills}
Required skills: {state.required_skills}
Skill gap: {state.skill_gap}

Return JSON:
{{
 "confidence":0-1
}}
"""

    response = llm.invoke([HumanMessage(content=prompt)]).content

    result = parse_json(response)

    confidence = result.get("confidence", state.evaluation_confidence)

    state.evaluation_confidence = confidence

    return state


# ===== Conditional Routing =====

def routing_decision(state: GraphState):

    if state.evaluation_confidence and state.evaluation_confidence < 0.6:
        return "HumanReview"

    if state.eligible:
        return "Eligible"

    if len(state.skill_gap) <= 3:
        return "SuggestPlan"

    return "HumanReview"


# ===== Node 5 — Suggest Learning Plan =====

def suggest_plan(state: GraphState):

    prompt = f"""
Create a short learning plan to improve these skills:

{state.skill_gap}

Keep it concise.
"""

    response = llm.invoke([HumanMessage(content=prompt)]).content

    state.improvement_plan = response if isinstance(response, str) else str(response)

    return state


# ===== Node 6 — Human Review =====

def human_review(state: GraphState) -> Command:

    action = interrupt(

        CreateTask(
            app_name="InternshipEligibilityReview",
            title="Review Internship Eligibility",
            data={
                "Student Profile": state.student_profile,
                "Role": state.internship_role,
                "Detected Skills": ", ".join(state.extracted_skills),
                "Skill Gap": ", ".join(state.skill_gap)
            }
        )
    )

    decision = ""

    if isinstance(action, dict):
        decision = action.get("Decision", "")

    update = {
        "eligible": decision.lower() == "approve"
    }

    return Command(update=update)


# ===== Node 7 — Output =====

def generate_output(state: GraphState):

    result = {

        "eligible": state.eligible,

        "student_skills": state.extracted_skills,

        "required_skills": state.required_skills,

        "skill_gap": state.skill_gap,

        "improvement_plan": state.improvement_plan,

        "confidence": state.evaluation_confidence
    }

    print(json.dumps(result, indent=2))

    return state


# ===== Build Graph =====

graph = StateGraph(GraphState)

graph.add_node("ExtractSkills", extract_student_skills)
graph.add_node("ExtractRoleSkills", extract_required_skills)
graph.add_node("EvaluateEligibility", evaluate_eligibility)
graph.add_node("SelfEvaluate", self_evaluate)
graph.add_node("SuggestPlan", suggest_plan)
graph.add_node("HumanReview", human_review)
graph.add_node("Output", generate_output)


graph.add_edge(START, "ExtractSkills")
graph.add_edge("ExtractSkills", "ExtractRoleSkills")
graph.add_edge("ExtractRoleSkills", "EvaluateEligibility")
graph.add_edge("EvaluateEligibility", "SelfEvaluate")


graph.add_conditional_edges(

    "SelfEvaluate",

    routing_decision,

    {
        "Eligible": "Output",
        "SuggestPlan": "SuggestPlan",
        "HumanReview": "HumanReview"
    }
)

graph.add_edge("SuggestPlan", "Output")
graph.add_edge("HumanReview", "Output")

graph.add_edge("Output", END)

app = graph.compile()