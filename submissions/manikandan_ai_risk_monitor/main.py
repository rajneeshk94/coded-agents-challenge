from __future__ import annotations

from functools import lru_cache
from typing import Final, Literal

import langchain
import langgraph
import uipath_langchain
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from uipath_langchain.chat import UiPathChat

AGENT_NAME: Final[str] = "AI_AGENT_RISK_MONITOR"
RISK_LEVEL = Literal["LOW", "MEDIUM", "HIGH"]
_SDK_PACKAGES: Final[tuple[str, str, str]] = (
    langchain.__name__,
    langgraph.__name__,
    uipath_langchain.__name__,
)


class Input(BaseModel):
    action: str = Field(
        ...,
        min_length=1,
        description="The AI agent action to evaluate for operational risk.",
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Business and technical context describing what the action will do.",
    )


class AgentState(BaseModel):
    action: str = Field(..., description="The action being monitored.")
    description: str = Field(..., description="Context for the monitored action.")
    risk_level: RISK_LEVEL = Field(
        default="LOW",
        description="Risk classification emitted by the analyzer node.",
    )
    decision: str = Field(
        default="",
        description="Final decision produced after conditional routing.",
    )
    analysis: str = Field(
        default="",
        description="Concise explanation of why the action received its risk level.",
    )


class Output(BaseModel):
    action: str = Field(..., description="The evaluated action name.")
    risk_level: RISK_LEVEL = Field(..., description="LOW, MEDIUM, or HIGH.")
    analysis: str = Field(..., description="Structured explanation of the detected risk.")
    decision: str = Field(
        ...,
        description="Human Approval Required, Manual Review Recommended, or Safe to Execute.",
    )


class RiskAssessment(BaseModel):
    risk_level: RISK_LEVEL = Field(..., description="LOW, MEDIUM, or HIGH.")
    analysis: str = Field(..., min_length=8, description="Why the action is risky.")


@lru_cache(maxsize=1)
def get_llm() -> UiPathChat:
    return UiPathChat(model="gpt-4.1-mini-2025-04-14", temperature=0.0)


def heuristic_risk_assessment(action: str, description: str) -> RiskAssessment:
    text = f"{action} {description}".lower()

    high_patterns = {
        "transfer money": "Financial transfer to an external or uncontrolled destination detected.",
        "wire transfer": "Direct movement of funds detected.",
        "bank account": "Banking destination detected in the action context.",
        "external account": "Funds or data are moving to an external account.",
        "modify system settings": "Privileged system configuration change detected.",
        "system settings": "Privileged system configuration change detected.",
        "delete file": "Destructive file operation detected.",
        "delete files": "Destructive file operation detected.",
        "drop database": "Destructive database operation detected.",
        "disable security": "Security controls may be weakened by this action.",
        "reset password": "Credential-impacting action detected.",
    }
    for pattern, analysis in high_patterns.items():
        if pattern in text:
            return RiskAssessment(risk_level="HIGH", analysis=analysis)

    medium_patterns = {
        "access database": "Database access may expose sensitive or regulated information.",
        "query database": "Database access may expose sensitive or regulated information.",
        "send email": "Outbound communication can leak information or trigger unintended actions.",
        "external recipient": "External communication target increases data exposure risk.",
        "modify config": "Configuration change should be reviewed before execution.",
        "upload file": "File transfer can expose sensitive information.",
        "download file": "Data movement should be reviewed before execution.",
        "share document": "Document sharing may expose sensitive information.",
        "create user": "User lifecycle changes should be reviewed before execution.",
    }
    for pattern, analysis in medium_patterns.items():
        if pattern in text:
            return RiskAssessment(risk_level="MEDIUM", analysis=analysis)

    if "create meeting" in text:
        return RiskAssessment(
            risk_level="LOW",
            analysis="Calendar scheduling is a routine coordination task with limited blast radius.",
        )

    return RiskAssessment(
        risk_level="LOW",
        analysis="No destructive, privileged, financial, or sensitive-data indicators were detected.",
    )


def decision_for_risk_level(risk_level: RISK_LEVEL) -> str:
    return {
        "HIGH": "Human Approval Required",
        "MEDIUM": "Manual Review Recommended",
        "LOW": "Safe to Execute",
    }[risk_level]


def build_output(state: AgentState) -> Output:
    return Output(
        action=state.action,
        risk_level=state.risk_level,
        analysis=state.analysis,
        decision=state.decision,
    )


async def action_analyzer(state: AgentState) -> AgentState:
    system_prompt = (
        f"You are {AGENT_NAME}, a risk-monitoring agent for enterprise AI automation. "
        "Classify the requested action as LOW, MEDIUM, or HIGH risk. "
        "Return HIGH for destructive, privileged, financial, credential, or external-data actions. "
        "Return MEDIUM for actions needing oversight but not immediate human approval. "
        "Return LOW only for routine, reversible, low-impact actions. "
        "Provide one concise analysis sentence."
    )
    human_prompt = (
        f"Action: {state.action}\n"
        f"Description: {state.description}\n"
        "Respond with structured output only."
    )

    try:
        structured_llm = get_llm().with_structured_output(
            RiskAssessment,
            method="function_calling",
        )
        result = await structured_llm.ainvoke(
            [SystemMessage(system_prompt), HumanMessage(human_prompt)]
        )
        assessment = (
            result
            if isinstance(result, RiskAssessment)
            else RiskAssessment.model_validate(result)
        )
    except Exception:
        assessment = heuristic_risk_assessment(state.action, state.description)

    return state.model_copy(
        update={
            "analysis": assessment.analysis,
            "risk_level": assessment.risk_level,
        }
    )


async def decision_router(state: AgentState) -> AgentState:
    return state.model_copy(
        update={"decision": decision_for_risk_level(state.risk_level)}
    )


def route_by_risk_level(state: AgentState) -> str:
    return state.risk_level


async def human_approval_node(state: AgentState) -> Output:
    return build_output(state)


async def review_node(state: AgentState) -> Output:
    return build_output(state)


async def execute_node(state: AgentState) -> Output:
    return build_output(state)


builder = StateGraph(AgentState, input=Input, output=Output)

builder.add_node("action_analyzer", action_analyzer)
builder.add_node("decision_router", decision_router)
builder.add_node("human_approval_node", human_approval_node)
builder.add_node("review_node", review_node)
builder.add_node("execute_node", execute_node)

builder.add_edge(START, "action_analyzer")
builder.add_edge("action_analyzer", "decision_router")
builder.add_conditional_edges(
    "decision_router",
    route_by_risk_level,
    {
        "LOW": "execute_node",
        "MEDIUM": "review_node",
        "HIGH": "human_approval_node",
    },
)
builder.add_edge("execute_node", END)
builder.add_edge("review_node", END)
builder.add_edge("human_approval_node", END)

graph = builder.compile()
