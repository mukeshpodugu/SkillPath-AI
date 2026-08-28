from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from .database import engine, Base, get_db
from .models import User, Career, Skill, CareerSkill, KnowledgeState, LearningAction, UserActionLog, Question
from .schemas import (
    CareerResponse, UserOnboard, UserResponse, QuestionResponse, 
    DiagnosticSubmission, DashboardResponse, ActionCompleteRequest, KnowledgeStateResponse,
    NBLARecommendationResponse, LearningActionResponse, NBLAExplanation
)
from .seed import seed_data
from .optimizer import get_next_best_learning_action

# Initialize Database
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SkillPath AI API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Seed database on startup
@app.on_event("startup")
def startup_event():
    db = next(get_db())
    seed_data(db)

@app.get("/api/careers", response_model=List[CareerResponse])
def get_careers(db: Session = Depends(get_db)):
    return db.query(Career).all()

@app.post("/api/users/onboard")
def onboard_user(data: UserOnboard, db: Session = Depends(get_db)):
    # 1. Verify Career
    career = db.query(Career).filter(Career.id == data.target_career_id).first()
    if not career:
        raise HTTPException(status_code=400, detail="Target career not found.")
        
    # 2. Create User
    user = User(name=data.name, target_career_id=data.target_career_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # 3. Initialize all career skills in KnowledgeState with 0.0
    career_skills = db.query(CareerSkill).filter(CareerSkill.career_id == data.target_career_id).all()
    for cs in career_skills:
        ks = KnowledgeState(user_id=user.id, skill_id=cs.skill_id, mastery=0.0)
        db.add(ks)
    db.commit()
    
    # 4. Fetch diagnostic questions for selected prior skills
    questions = db.query(Question).filter(
        Question.skill_id.in_(data.known_skill_ids)
    ).all()
    
    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "target_career_id": user.target_career_id
        },
        "questions": [
            {
                "id": q.id,
                "skill_id": q.skill_id,
                "text": q.text,
                "option_a": q.option_a,
                "option_b": q.option_b,
                "option_c": q.option_c,
                "option_d": q.option_d
            } for q in questions
        ]
    }

@app.post("/api/users/{user_id}/diagnostic")
def submit_diagnostic(user_id: int, submission: DiagnosticSubmission, db: Session = Depends(get_db)):
    # 1. Fetch User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    # 2. Score questions per skill
    answers = submission.answers
    if not answers:
        return {"status": "success", "message": "No answers submitted. Initialized mastery to 0.0"}
        
    skill_results = {} # skill_id -> {correct: int, total: int}
    
    for ans in answers:
        q = db.query(Question).filter(Question.id == ans.question_id).first()
        if not q:
            continue
            
        if q.skill_id not in skill_results:
            skill_results[q.skill_id] = {"correct": 0, "total": 0}
            
        skill_results[q.skill_id]["total"] += 1
        if ans.selected_option.upper() == q.correct_option.upper():
            skill_results[q.skill_id]["correct"] += 1
            
    # 3. Update KnowledgeStates based on scores
    for skill_id, stats in skill_results.items():
        score = stats["correct"] / stats["total"] if stats["total"] > 0 else 0.0
        # Cap score to realistic mastery (e.g. 0.3 for 1 correct, 0.65 for 2, 0.9 for 3)
        ks = db.query(KnowledgeState).filter(
            KnowledgeState.user_id == user_id,
            KnowledgeState.skill_id == skill_id
        ).first()
        if ks:
            ks.mastery = round(score * 0.9, 2) # set diagnostic max to 0.9
            db.add(ks)
            
    db.commit()
    return {
        "status": "success",
        "results": {
            skill_id: {
                "score": round(stats["correct"] / stats["total"], 2),
                "correct": stats["correct"],
                "total": stats["total"]
            } for skill_id, stats in skill_results.items()
        }
    }

@app.get("/api/users/{user_id}/dashboard", response_model=DashboardResponse)
def get_dashboard(user_id: int, db: Session = Depends(get_db)):
    # 1. Fetch User and Career
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    career = db.query(Career).filter(Career.id == user.target_career_id).first()
    if not career:
        raise HTTPException(status_code=400, detail="User has no target career.")
        
    # 2. Get knowledge states and career requirements
    career_skills = db.query(CareerSkill).filter(CareerSkill.career_id == career.id).all()
    ks_records = db.query(KnowledgeState).filter(KnowledgeState.user_id == user_id).all()
    ks_map = {ks.skill_id: ks.mastery for ks in ks_records}
    
    # 3. Compute Career Readiness Score
    sum_weighted_min = 0.0
    sum_weighted_req = 0.0
    
    skills_states = []
    for cs in career_skills:
        curr_mastery = ks_map.get(cs.skill_id, 0.0)
        req_mastery = cs.required_mastery
        importance = cs.importance
        
        sum_weighted_min += importance * min(curr_mastery, req_mastery)
        sum_weighted_req += importance * req_mastery
        
        skills_states.append(KnowledgeStateResponse(
            skill_id=cs.skill_id,
            skill_name=cs.skill.name,
            mastery=curr_mastery,
            required_mastery=req_mastery,
            importance=importance
        ))
        
    career_readiness = sum_weighted_min / sum_weighted_req if sum_weighted_req > 0.0 else 0.0
    career_readiness = round(career_readiness, 2)
    
    # 4. Get NBLA Recommendation
    nbla_result = get_next_best_learning_action(db, user_id, career.id)
    next_best_action = None
    
    if nbla_result:
        action, score, components, explanation = nbla_result
        next_best_action = NBLARecommendationResponse(
            action=LearningActionResponse(
                id=action.id,
                title=action.title,
                description=action.description,
                skill_id=action.skill_id,
                skill_name=action.skill.name,
                action_type=action.action_type,
                expected_gain=action.expected_gain,
                learning_effort=action.learning_effort,
                url=action.url
            ),
            action_score=round(score, 3),
            explanation=NBLAExplanation(
                summary=explanation,
                components=components
            )
        )
        
    return DashboardResponse(
        career_readiness=career_readiness,
        career_name=career.name,
        skills_states=skills_states,
        next_best_action=next_best_action
    )

@app.post("/api/users/{user_id}/actions/{action_id}/complete")
def complete_action(user_id: int, action_id: int, req: ActionCompleteRequest, db: Session = Depends(get_db)):
    # 1. Fetch User and Action
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    action = db.query(LearningAction).filter(LearningAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Learning action not found.")
        
    # 2. Log completion
    log = UserActionLog(user_id=user_id, action_id=action_id, performance_score=req.performance_score)
    db.add(log)
    
    # 3. Update KnowledgeState
    ks = db.query(KnowledgeState).filter(
        KnowledgeState.user_id == user_id,
        KnowledgeState.skill_id == action.skill_id
    ).first()
    
    if not ks:
        ks = KnowledgeState(user_id=user_id, skill_id=action.skill_id, mastery=0.0)
        db.add(ks)
        
    # Calculate gain based on action type and score
    gain = action.expected_gain
    if action.action_type == "ASSESSMENT" and req.performance_score is not None:
        # Directly use performance score for assessment
        ks.mastery = round(req.performance_score, 2)
    else:
        # Otherwise increment mastery
        ks.mastery = min(1.0, round(ks.mastery + gain, 2))
        
    db.commit()
    
    # Return updated dashboard
    return get_dashboard(user_id=user_id, db=db)
