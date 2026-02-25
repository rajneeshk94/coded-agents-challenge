# 🚀 UiPath Coded Agent Challenge

Welcome to the **UiPath Coded Agent Challenge**.

After seeing the AutoTA demo, your task is to build your own **Coded Agent** using:

- UiPath Python SDK
- LangGraph
- Structured agent state
- Conditional routing

This is **NOT** a chatbot challenge.

You must build a real **agentic system** that can be deployed and run using the UiPath SDK.

---

# 🎯 Challenge Objective

Build a real-world **agentic solution** that:

- Uses LangGraph for orchestration
- Uses UiPath SDK for deployment & integration
- Defines structured states
- Includes conditional routing
- Produces structured output
- Can be deployed as a Coded Agent

Your agent should demonstrate autonomous decision-making behavior.

---

# 📚 Getting Started (Mandatory Reference)

Before building your solution, review the official UiPath documentation:

👉 https://uipath.github.io/uipath-python/langchain/quick_start/

Your submission must follow the principles and setup described in this guide.

---

# 🧠 What Counts as Agentic?

Your solution must include at least **ONE** of the following:

- Conditional routing
- Tool selection logic
- Retry mechanism
- Self-evaluation step
- Human-in-the-loop integration
- Multi-step reasoning

If your project is simply:

Input → LLM → Output

It will **NOT** qualify.

---

# 🛠️ Technical Requirements

Your submission must:

- Use LangGraph
- Define a `GraphState`
- Include at least 2 nodes
- Include at least 1 conditional edge
- Use UiPath SDK for deployment
- Return structured output (JSON or object)

---

# 📦 Required Folder Structure

Inside the `submissions/` folder, create:
```
firstname_lastname/
    README.md
    [and the rest of your code files]
```

Example:
```
submissions/
    rajneesh_khare/
        main.py
        langgraph.json
        pyproject.toml
        uipath.json
        agent.mermaid
        README.md
```

---

# 📝 Submission Instructions

### Step 1 — Fork This Repository

Click **Fork** on GitHub.

### Step 2 — Clone Your Fork
git clone https://github.com/rajneeshk94/coded-agents-challenge.git


### Step 3 — Create a Branch
git checkout -b submission-yourname


### Step 4 — Add Your Agent

Create your folder inside `submissions/` folder and place all your code files


### Step 5 — Commit & Push
 - git add .
 - git commit -m "Added my coded agent submission"
 - git push origin submission-yourname


### Step 6 — Create Pull Request

Open a Pull Request to the `main` branch of this repository.

Your submission will be reviewed before merging.

---

# 📊 Evaluation Criteria

| Criteria                          | Weight |
|-----------------------------------|--------|
| Agentic Design                   | 25%    |
| Proper LangGraph Usage           | 15%    |
| UiPath SDK Integration           | 20%    |
| Code Quality & Structure         | 15%    |
| Creativity & Usefulness          | 15%    |
| Documentation & Clarity          | 10%    |

---

# 🎨 Creativity & Usefulness

Your agent should:

- Solve a meaningful real-world problem  
- Be practical or relatable  
- Show thoughtful design  
- Demonstrate innovation beyond basic examples  

Creative and useful solutions will receive higher scores.

---

# 📘 Your Submission README Must Include

Inside your personal submission folder, include a `README.md` with:

- 🧠 Use Case Description
- 🎯 Goal of the Agent
- 🔄 Agent Flow Explanation
- 🛠️ Tools Used
- 🧪 Example Input
- 📤 Example Output

Optional but recommended:

- Mermaid flow diagram
- Architecture explanation
- Demo video link

---

# 💡 Example Use Case Ideas

You may build agents such as:

- 📚 Assignment Evaluation Agent  
- 📝 Resume Reviewer for Campus Placements  
- 🎯 Internship Eligibility Checker  
- 🏠 Hostel Leave Approval Agent  
- 💰 Student Budget Planning Agent  
- 📅 Exam Preparation Strategy Agent  
- 🧾 Project Proposal Reviewer  
- 🧠 Skill Gap Analyzer for Placements  
- 📦 Hackathon Idea Validation Agent  
- 📊 Academic Performance Risk Analyzer  

You are free to innovate beyond these ideas.

You can also refer to this example:

👉 https://github.com/rajneeshk94/LeaveRequestAgent

---

# 🚫 Disqualification Rules

Submissions will be rejected if they:

- Do not use LangGraph
- Do not use UiPath SDK
- Are single-node LLM wrappers
- Have no routing logic
- Contain broken or non-runnable code

---

Build something intelligent.

Good luck 🚀
