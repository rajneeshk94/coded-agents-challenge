# 👕 Campus Style Agent

A multi-agent wardrobe recommendation system built using **UiPath Coded Agents and LangGraph**.

The agent helps students choose an appropriate outfit based on:

- Event type
- Weather conditions
- Available wardrobe items

It combines **rule-based reasoning and LLM-based explanations** to recommend the most suitable outfit.

---

# 🧠 Agent Architecture

The system uses a **multi-agent pipeline**:

Context Agent → Wardrobe Agent → Outfit Generator → Style Reasoning Agent

### Agents

**Context Agent**
Classifies the situation as formal or casual.

**Wardrobe Agent**
Categorizes wardrobe items into tops and bottoms.

**Outfit Generator**
Generates outfit combinations and scores them based on suitability.

**Style Reasoning Agent**
Uses an LLM to explain why the recommended outfit is appropriate.

---

# ⚙️ Technologies Used

- UiPath Coded Agents SDK
- LangGraph
- LangChain
- Azure OpenAI (via UiPath)

---

# 📥 Input Example

```json
{
  "event": "presentation",
  "weather": "hot",
  "wardrobe": [
    "white shirt",
    "black shirt",
    "blue jeans",
    "white pants"
  ]
}

Output example:

recommended_outfit: white shirt + blue jeans
confidence: 0.8

alternatives:
- white shirt + white pants
- black shirt + blue jeans

explanation:
A white shirt provides a professional appearance suitable for a presentation while jeans keep the outfit comfortable in warm weather.
