"""
Smart Email Triage & Draft Agent
Uses LangGraph for orchestration + UiPath SDK for deployment
"""

from typing import Literal
from pydantic import BaseModel, Field
from langgraph.graph import END, START, StateGraph
from langchain_core.messages import HumanMessage, SystemMessage
from uipath_langchain.chat import UiPathChat

# ─────────────────────────────────────────────
# LLM Setup (UiPath LLM Gateway — no API key needed)
# ─────────────────────────────────────────────
llm = UiPathChat(model="gpt-4o-2024-08-06", temperature=0)

# ─────────────────────────────────────────────
# Structured State Definition
# ─────────────────────────────────────────────
class Input(BaseModel):
    """Input schema: the raw email to be processed."""
    email_subject: str = Field(description="Subject line of the email")
    email_body: str = Field(description="Body content of the email")
    sender: str = Field(description="Sender's email address")


class Output(BaseModel):
    """Structured output: triage result + action taken."""
    category: Literal["urgent", "normal", "spam"] = Field(
        description="Classified category of the email"
    )
    action: Literal["escalate", "draft_reply", "discard"] = Field(
        description="Action taken by the agent"
    )
    draft_reply: str = Field(
        default="", description="Draft reply generated (empty if spam)"
    )
    escalation_note: str = Field(
        default="", description="Note added if email is urgent"
    )
    confidence_score: float = Field(
        description="Agent self-evaluation confidence (0.0 - 1.0)"
    )
    reasoning: str = Field(description="Why the agent made this decision")


class State(BaseModel):
    """Internal graph state passed between nodes."""
    # Inputs
    email_subject: str = ""
    email_body: str = ""
    sender: str = ""
    # Intermediate
    category: str = ""
    draft_reply: str = ""
    escalation_note: str = ""
    reasoning: str = ""
    confidence_score: float = 0.0
    retry_count: int = 0
    # Output
    action: str = ""


# ─────────────────────────────────────────────
# NODE 1: Classify Email
# ─────────────────────────────────────────────
async def classify_node(state: State) -> State:
    """Reads the email and classifies it as urgent / normal / spam."""
    messages = [
        SystemMessage(content="""You are an email classification assistant.
Classify the email into exactly ONE category:
- urgent: requires immediate attention (complaints, legal, system down, angry customer)
- normal: standard business email needing a reply
- spam: promotional, irrelevant, or junk

Respond ONLY with a JSON object like:
{"category": "urgent", "reasoning": "Customer is threatening to cancel contract"}
"""),
        HumanMessage(content=f"""
From: {state.sender}
Subject: {state.email_subject}
Body: {state.email_body}
""")
    ]
    response = await llm.ainvoke(messages)
    import json, re
    # Parse JSON from LLM response
    match = re.search(r'\{.*\}', response.content, re.DOTALL)
    if match:
        data = json.loads(match.group())
        state.category = data.get("category", "normal")
        state.reasoning = data.get("reasoning", "")
    else:
        state.category = "normal"
        state.reasoning = "Could not parse classification, defaulting to normal."
    return state


# ─────────────────────────────────────────────
# NODE 2: Draft Reply (for normal emails)
# ─────────────────────────────────────────────
async def draft_reply_node(state: State) -> State:
    """Generates a professional draft reply for normal emails."""
    messages = [
        SystemMessage(content="""You are a professional email assistant.
Write a concise, polite, professional reply to this email.
Keep it under 100 words. Be helpful and clear."""),
        HumanMessage(content=f"""
From: {state.sender}
Subject: {state.email_subject}
Body: {state.email_body}
""")
    ]
    response = await llm.ainvoke(messages)
    state.draft_reply = response.content.strip()
    state.action = "draft_reply"
    state.confidence_score = 0.85
    return state


# ─────────────────────────────────────────────
# NODE 3: Escalate + Draft (for urgent emails)
# ─────────────────────────────────────────────
async def escalate_node(state: State) -> State:
    """Drafts an urgent reply and adds an escalation note."""
    messages = [
        SystemMessage(content="""You are a senior customer success manager.
This email is URGENT. Write a reply that:
1. Acknowledges urgency immediately
2. Is empathetic and professional
3. Promises concrete next steps
4. Is under 120 words

Also write a short ESCALATION NOTE (1 sentence) for the manager."""),
        HumanMessage(content=f"""
From: {state.sender}
Subject: {state.email_subject}
Body: {state.email_body}

Return ONLY valid JSON:
{{
  "draft_reply": "...",
  "escalation_note": "...",
  "confidence_score": 0.0
}}
""")
    ]
    response = await llm.ainvoke(messages)
    import json, re
    match = re.search(r'\{.*\}', response.content, re.DOTALL)
    if match:
        data = json.loads(match.group())
        state.draft_reply = data.get("draft_reply", "")
        state.escalation_note = data.get("escalation_note", "")
        state.confidence_score = float(data.get("confidence_score", 0.7))
    else:
        state.draft_reply = response.content.strip()
        state.escalation_note = "Manual review required."
        state.confidence_score = 0.5

    # ── Self-evaluation: retry if confidence too low ──
    if state.confidence_score < 0.6 and state.retry_count < 2:
        state.retry_count += 1
        return await escalate_node(state)  # Retry

    state.action = "escalate"
    return state


# ─────────────────────────────────────────────
# NODE 4: Discard (for spam)
# ─────────────────────────────────────────────
async def discard_node(state: State) -> State:
    """Marks spam emails for discarding — no reply generated."""
    state.draft_reply = ""
    state.escalation_note = ""
    state.action = "discard"
    state.confidence_score = 0.95
    return state


# ─────────────────────────────────────────────
# NODE 5: Output
# ─────────────────────────────────────────────
async def output_node(state: State) -> Output:
    """Converts the internal state to the final structured output."""
    return Output(
        category=state.category,
        action=state.action,
        draft_reply=state.draft_reply,
        escalation_note=state.escalation_note,
        confidence_score=state.confidence_score,
        reasoning=state.reasoning
    )


# ─────────────────────────────────────────────
# CONDITIONAL ROUTING
# ─────────────────────────────────────────────
def route_by_category(state: State) -> Literal["draft_reply", "escalate", "discard"]:
    """Routes to the right node based on email category."""
    routing_map = {
        "urgent": "escalate",
        "normal": "draft_reply",
        "spam":   "discard",
    }
    return routing_map.get(state.category, "draft_reply")


# ─────────────────────────────────────────────
# BUILD THE GRAPH
# ─────────────────────────────────────────────
def build_graph():
    builder = StateGraph(State, input=Input, output=Output)

    # Add nodes
    builder.add_node("classify",    classify_node)
    builder.add_node("draft_reply", draft_reply_node)
    builder.add_node("escalate",    escalate_node)
    builder.add_node("discard",     discard_node)
    builder.add_node("output",      output_node)

    # Entry point
    builder.add_edge(START, "classify")

    # Conditional routing from classify → one of three paths
    builder.add_conditional_edges(
        "classify",
        route_by_category,
        {
            "draft_reply": "draft_reply",
            "escalate":    "escalate",
            "discard":     "discard",
        }
    )

    # All paths lead to output
    builder.add_edge("draft_reply", "output")
    builder.add_edge("escalate",    "output")
    builder.add_edge("discard",     "output")
    builder.add_edge("output",      END)

    return builder.compile()


# Export graph for UiPath
graph = build_graph()
