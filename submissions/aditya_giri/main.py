from langgraph.graph import StateGraph
from state import StyleState
from agents import context_agent, wardrobe_agent, outfit_agent, style_reasoning_agent


builder = StateGraph(StyleState)

builder.add_node("context", context_agent)
builder.add_node("wardrobe", wardrobe_agent)
builder.add_node("outfit", outfit_agent)
builder.add_node("style_reasoning", style_reasoning_agent)

builder.set_entry_point("context")

builder.add_edge("context", "wardrobe")
builder.add_edge("wardrobe", "outfit")
builder.add_edge("outfit", "style_reasoning")

graph = builder.compile()


def run( input):

    state = {
        "event": input["event"],
        "weather": input["weather"],
        "wardrobe": input["wardrobe"],
        "tops": [],
        "bottoms": [],
        "context": "",
        "outfit": "",
        "alternatives": [],
        "confidence": 0,
        "explanation": ""
    }

    result = graph.invoke(state)

    return {
        "recommended_outfit": result["outfit"],
        "confidence": result["confidence"],
        "alternatives": result["alternatives"],
        "explanation": result["explanation"]
    }