from uipath_langchain.chat.models import UiPathAzureChatOpenAI
from langchain_core.messages import HumanMessage

# Initialize LLM
llm = UiPathAzureChatOpenAI(
    model="gpt-4o-2024-08-06",
    temperature=0,
    max_tokens=2000,
    timeout=30,
    max_retries=2
)

def context_agent(state):

    event = state["event"]

    if event in ["presentation", "interview"]:
        state["context"] = "formal"
    else:
        state["context"] = "casual"

    return state


def categorize(item):

    item = item.lower()

    if "shirt" in item:
        return "top"

    if "jeans" in item or "pants" in item:
        return "bottom"

    return "other"


def wardrobe_agent(state):

    tops = []
    bottoms = []

    for item in state["wardrobe"]:

        category = categorize(item)

        if category == "top":
            tops.append(item)

        if category == "bottom":
            bottoms.append(item)

    state["tops"] = tops
    state["bottoms"] = bottoms

    return state


def outfit_agent(state):

    outfits = []

    for t in state["tops"]:
        for b in state["bottoms"]:

            score = 0.5

            if state["context"] == "formal" and "shirt" in t:
                score += 0.3

            outfits.append((f"{t} + {b}", score))

    outfits.sort(key=lambda x: x[1], reverse=True)

    best = outfits[0]

    state["outfit"] = best[0]
    state["confidence"] = best[1]

    state["alternatives"] = [o[0] for o in outfits[1:3]]

    return state

def style_reasoning_agent(state):

    prompt = f"""
Role:
You are a campus fashion advisor helping students choose appropriate outfits.

Goal:
Evaluate whether the outfit is suitable for the given event and weather.

Instructions:
- Consider professionalism for presentations and interviews.
- Consider comfort for casual events.
- Consider weather conditions.
- Provide a short explanation.

Steps:
1. Understand the event.
2. Consider weather conditions.
3. Evaluate the outfit combination.
4. Provide reasoning.

Example:
Event: presentation
Weather: hot
Outfit: white shirt + blue jeans

Explanation:
A white shirt provides a professional appearance while jeans keep the outfit comfortable in warm weather.

Now evaluate:

Event: {state["event"]}
Weather: {state["weather"]}
Outfit: {state["outfit"]}
"""

    response = llm.invoke([HumanMessage(content=prompt)])

    state["explanation"] = response.content

    return state