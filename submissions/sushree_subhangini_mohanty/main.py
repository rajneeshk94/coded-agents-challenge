from typing import List, Literal, Dict
from datetime import datetime
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, StateGraph, END
from uipath_langchain.chat import UiPathChat
from pydantic import BaseModel

# LLM
llm = UiPathChat(model="gpt-4o-mini-2024-07-18")


# ---------------- STATE ----------------

class GraphState(BaseModel):
    subjects: List[str]
    exam_dates: List[str]
    preparation_level: Literal["low", "medium", "high"]
    daily_hours: int
    weak_subjects: List[str]

    risk_level: str | None = None
    study_plan: str | None = None
    plan_quality: str | None = None

    urgency_scores: Dict[str, float] | None = None
    time_distribution: Dict[str, float] | None = None


class GraphOutput(BaseModel):
    risk_level: str
    study_plan: str


# ---------------- NODE 1: ANALYZE RISK + URGENCY ----------------

async def analyze_risk(state: GraphState) -> GraphState:
    """
    Hybrid reasoning step:
    - Mathematical urgency scoring
    - Weak subject weighting
    - Time redistribution calculation
    """

    today = datetime.today()

    urgency_scores = {}
    total_score = 0

    for subject, exam_date in zip(state.subjects, state.exam_dates):
        exam_dt = datetime.strptime(exam_date, "%Y-%m-%d")

        days_remaining = max((exam_dt - today).days, 1)

        # urgency increases as exam approaches
        score = 1 / days_remaining

        # boost weak subjects
        if subject in state.weak_subjects:
            score *= 1.5

        urgency_scores[subject] = score
        total_score += score

    # normalize distribution
    time_distribution = {
        subject: round(score / total_score, 2)
        for subject, score in urgency_scores.items()
    }

    # risk calculation
    highest_load = max(time_distribution.values())

    if highest_load > 0.45:
        risk = "high"
    elif highest_load > 0.30:
        risk = "medium"
    else:
        risk = "low"

    return state.model_copy(update={
        "risk_level": risk,
        "urgency_scores": urgency_scores,
        "time_distribution": time_distribution
    })


# ---------------- NODE 2: GENERATE PLAN ----------------

async def generate_plan(state: GraphState) -> GraphState:
    """
    LLM generates a study plan guided by computed time distribution.
    """

    system_prompt = """
You are an expert academic planning assistant.

You must generate realistic study schedules based on:
- subject urgency
- weak subjects
- daily available hours

The plan must strictly follow the provided time distribution.
"""

    user_prompt = f"""
Subjects: {state.subjects}

Computed Time Distribution (percentage of study time):
{state.time_distribution}

Weak Subjects: {state.weak_subjects}

Daily Study Hours Available: {state.daily_hours}

Risk Level: {state.risk_level}

Generate a clear weekly study plan with:
- daily breakdown
- revision slots
- focus on weak subjects
"""

    response = await llm.ainvoke([
        SystemMessage(system_prompt),
        HumanMessage(user_prompt)
    ])

    return state.model_copy(update={
        "study_plan": response.content
    })


# ---------------- NODE 3: SELF EVALUATION ----------------

async def self_evaluate_plan(state: GraphState) -> GraphState:
    """
    Agent critiques its own generated plan.
    """

    system_prompt = """
You are a strict academic strategy reviewer.

Evaluate the following study plan.

Return ONLY one word:
good
or
poor

Mark 'poor' if:
- unrealistic for given hours
- lacks revision
- poor structure
- ignores weak subjects
"""

    response = await llm.ainvoke([
        SystemMessage(system_prompt),
        HumanMessage(state.study_plan or "")
    ])

    quality = response.content.strip().lower()

    if quality not in ["good", "poor"]:
        quality = "good"

    return state.model_copy(update={
        "plan_quality": quality
    })


# ---------------- NODE 4: IMPROVE PLAN ----------------

async def improve_plan(state: GraphState) -> GraphState:
    """
    If evaluation fails, improve the plan.
    """

    system_prompt = """
Improve the following study plan.

Requirements:
- realistic schedule
- balanced workload
- include revision
- respect daily hour limits
"""

    response = await llm.ainvoke([
        SystemMessage(system_prompt),
        HumanMessage(state.study_plan or "")
    ])

    return state.model_copy(update={
        "study_plan": response.content
    })


# ---------------- ROUTING ----------------

def route_after_risk(state: GraphState):
    return "generate_plan"


def route_after_evaluation(state: GraphState):
    if state.plan_quality == "poor":
        return "improve_plan"
    return END


# ---------------- BUILD GRAPH ----------------

builder = StateGraph(GraphState, output=GraphOutput)

builder.add_node("analyze_risk", analyze_risk)
builder.add_node("generate_plan", generate_plan)
builder.add_node("self_evaluate_plan", self_evaluate_plan)
builder.add_node("improve_plan", improve_plan)

builder.add_edge(START, "analyze_risk")

builder.add_conditional_edges(
    "analyze_risk",
    route_after_risk
)

builder.add_edge("generate_plan", "self_evaluate_plan")

builder.add_conditional_edges(
    "self_evaluate_plan",
    route_after_evaluation,
    path_map={
        "improve_plan": "improve_plan",
        END: END
    }
)

builder.add_edge("improve_plan", "self_evaluate_plan")

graph = builder.compile()
