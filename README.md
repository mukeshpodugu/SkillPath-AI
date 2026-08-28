# SkillPath AI: Career-Aware Adaptive Learning Path Optimization

This is the prototype implementation of **SkillPath AI** (also referred to as **EduPath AI**), an intelligent learning platform that dynamically recommends the **Next Best Learning Action (NBLA)** for a learner to efficiently achieve a targeted career goal.

This prototype demonstrates the exact workflow and scoring mechanics presented in the Capstone Review - I:
1. **User Profiling & Career Target Selection** (e.g. Machine Learning Engineer, Frontend Developer, Data Scientist)
2. **Prior Knowledge Selection**
3. **Dynamic Diagnostic Assessment Exam** (Quiz wizard testing claimed skills)
4. **Knowledge State Estimation** ($M_{curr}$ initialization)
5. **Skill Gap Engine** ($SkillGap = \max(0, M_{req} - M_{curr})$)
6. **Prerequisite Graph Constraint Enforcement** (via Directed Acyclic Graph)
7. **NBLA Optimization & Explanation Engine**

---

## Technical Stack
- **Frontend**: React (Vite) + Lucide Icons + Embed CSS
- **Backend API**: Python + FastAPI + Uvicorn
- **Database**: SQLite (SQLAlchemy ORM)
- **ML / Optimizer**: NBLA Scorer & Explainability Generator

---

## How to Run the Project

Your system must have Python 3.x and Node.js (npm) installed. 

### 1. Launch the Backend API
1. Navigate to the `backend/` folder.
2. Double-click or run `run.bat` in your terminal.
   * This script will automatically install the requirements (`fastapi`, `uvicorn`, `sqlalchemy`) and start the local server on **`http://localhost:8000`**.
   * It seeds the database automatically on startup with career paths, prerequisite networks, and exam questions.

### 2. Launch the Frontend UI
1. Navigate to the `frontend/` folder.
2. Double-click or run `run.bat` in your terminal.
   * This script will run `npm install` to download dependencies and then start the development server on **`http://localhost:5173`**.
3. Open your browser and navigate to `http://localhost:5173`.

---

## Core Algorithm: Next Best Learning Action (NBLA)

The system computes the recommendation score for each learning resource/activity targeting a skill $s$ using the multi-factor optimization formula:

$$ActionScore(a) = \alpha \cdot SkillGap(s) + \beta \cdot I_c(s) + \gamma \cdot P_{val}(s) + \delta \cdot ExpectedGain(a) - \lambda \cdot LearningEffort(a)$$

Where:
- $SkillGap(s)$: Current gap between required role mastery and user's current mastery level.
- $I_c(s)$: Career Importance rating of the skill for the selected role.
- $P_{val}(s)$: Prerequisite value of the skill, representing the sum of importances of all unmet downstream skills that depend on this skill.
- $ExpectedGain(a)$: Estimated growth in mastery from completing the action.
- $LearningEffort(a)$: Estimated time/difficulty of the action (acting as a penalty, subtracted).

**Explainability Engine**: The system identifies the dominant scoring components contributing to the NBLA score and presents a natural-language description explaining the rationale behind the recommendation in real-time.
