from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from .database import engine, Base, get_db
from .models import (
    User, LearnerProfile, Career, Skill, CareerSkill, 
    KnowledgeState, LearningAction, UserActionLog, Question,
    LearningModule, LearningResource, UserResourceProgress
)
from .schemas import (
    CareerResponse, UserOnboard, UserResponse, QuestionResponse, 
    DiagnosticSubmission, DashboardResponse, ActionCompleteRequest, KnowledgeStateResponse,
    NBLARecommendationResponse, LearningActionResponse, NBLAExplanation,
    UserRegister, UserLogin, TokenResponse, UserProfileUpdate,
    CareerRecommendationItem, RoadmapResponse, ResourceStatusUpdate,
    ExamStartResponse, ExamSubmissionRequest, ExamResultResponse,
    CreateOrderRequest, OrderResponse, VerifyPaymentRequest, PlanResponse
)
from .seed import seed_data
from .optimizer import get_next_best_learning_action
from .auth import (
    hash_password, verify_password, create_access_token, 
    get_current_user, get_optional_user, require_admin
)
from .career_recommender import recommend_careers_for_learner
from .roadmap import get_learner_roadmap
from .exams import start_module_exam, evaluate_module_exam
from .payments import get_plans, create_razorpay_order, verify_razorpay_payment
from .email_service import send_welcome_email
from .admin import router as admin_router
from .research_eval import router as research_router

# Initialize Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="EduPath AI API",
    description="Career-Aware Adaptive Learning Path Optimization Platform with Knowledge Tracing and NBLA Intelligence",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Modular Routers
app.include_router(admin_router)
app.include_router(research_router)

@app.on_event("startup")
def startup_event():
    db = next(get_db())
    seed_data(db)

@app.get("/")
def root_endpoint():
    return {
        "platform": "EduPath AI",
        "status": "online",
        "version": "2.0.0",
        "docs_url": "/docs"
    }

# ================= AUTHENTICATION ENDPOINTS =================

@app.post("/api/auth/register", response_model=TokenResponse)
def register_user(data: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email.lower().strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email address already exists.")

    user = User(
        name=data.name.strip(),
        email=data.email.lower().strip(),
        password_hash=hash_password(data.password),
        role=data.role if data.role in ["student", "admin"] else "student",
        is_email_verified=True,
        subscription_tier="free"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Initialize empty profile
    profile = LearnerProfile(user_id=user.id)
    db.add(profile)
    db.commit()

    send_welcome_email(db, user.id, user.name, user.email)
    token = create_access_token(user.id, user.role, user.email)
    return TokenResponse(access_token=token, user=user)

@app.post("/api/auth/login", response_model=TokenResponse)
def login_user(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower().strip()).first()
    if not user or not user.password_hash:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token(user.id, user.role, user.email)
    return TokenResponse(access_token=token, user=user)

@app.get("/api/auth/me", response_model=UserResponse)
def get_current_user_profile(user: User = Depends(get_current_user)):
    return user

@app.put("/api/auth/profile", response_model=UserResponse)
def update_learner_profile(
    data: UserProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if data.name:
        user.name = data.name.strip()

    profile = user.profile
    if not profile:
        profile = LearnerProfile(user_id=user.id)
        db.add(profile)

    for field, val in data.dict(exclude_unset=True).items():
        if field != "name" and hasattr(profile, field) and val is not None:
            setattr(profile, field, val)

    db.commit()
    db.refresh(user)
    return user

# ================= CAREER SELECTION & RECOMMENDATIONS =================

@app.get("/api/careers", response_model=List[CareerResponse])
def get_all_careers(db: Session = Depends(get_db)):
    careers = db.query(Career).all()
    results = []
    for c in careers:
        skills = []
        for cs in c.skills:
            skills.append({
                "skill_id": cs.skill_id,
                "skill_name": cs.skill.name,
                "category": cs.skill.category,
                "required_mastery": cs.required_mastery,
                "importance": cs.importance
            })
        results.append(CareerResponse(
            id=c.id,
            name=c.name,
            description=c.description,
            onet_soc_code=c.onet_soc_code,
            typical_salary_range=c.typical_salary_range,
            market_growth_rate=c.market_growth_rate,
            skills=skills
        ))
    return results

@app.get("/api/careers/recommendations", response_model=List[CareerRecommendationItem])
def get_career_recommendations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI-powered matching connecting learner background with O*NET career roles."""
    return recommend_careers_for_learner(db, user)

@app.post("/api/careers/select/{career_id}", response_model=UserResponse)
def select_target_career(
    career_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    career = db.query(Career).filter(Career.id == career_id).first()
    if not career:
        raise HTTPException(status_code=404, detail="Career not found.")

    user.target_career_id = career.id

    # Initialize knowledge states for skills in this career if not present
    for cs in career.skills:
        ks = db.query(KnowledgeState).filter(
            KnowledgeState.user_id == user.id,
            KnowledgeState.skill_id == cs.skill_id
        ).first()
        if not ks:
            db.add(KnowledgeState(user_id=user.id, skill_id=cs.skill_id, mastery=0.0))

    db.commit()
    db.refresh(user)
    return user

# ================= ADAPTIVE ROADMAP & RESOURCES =================

@app.get("/api/roadmap", response_model=RoadmapResponse)
def get_roadmap(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    roadmap = get_learner_roadmap(db, user)
    if not roadmap:
        raise HTTPException(status_code=400, detail="Please select a target career first to generate your roadmap.")
    return roadmap

@app.post("/api/resources/{resource_id}/status")
def update_resource_status(
    resource_id: int,
    data: ResourceStatusUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resource = db.query(LearningResource).filter(LearningResource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found.")

    progress = db.query(UserResourceProgress).filter(
        UserResourceProgress.user_id == user.id,
        UserResourceProgress.resource_id == resource.id
    ).first()

    if not progress:
        progress = UserResourceProgress(user_id=user.id, resource_id=resource.id)
        db.add(progress)

    progress.status = data.status
    if data.minutes_spent > 0:
        progress.minutes_spent += data.minutes_spent
        user.total_study_minutes += data.minutes_spent

    db.commit()
    return {"status": "success", "resource_id": resource_id, "user_status": progress.status}

# ================= MODULE EXAMINATIONS =================

@app.get("/api/modules/{module_id}/exam", response_model=ExamStartResponse)
def get_module_examination(
    module_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return start_module_exam(db, module_id)

@app.post("/api/modules/{module_id}/exam/submit", response_model=ExamResultResponse)
def submit_module_examination(
    module_id: int,
    submission: ExamSubmissionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return evaluate_module_exam(db, user, module_id, submission)

# ================= DIAGNOSTIC ASSESSMENT (LEGACY & EXTENDED) =================

@app.post("/api/users/onboard")
def onboard_user(data: UserOnboard, db: Session = Depends(get_db)):
    career = db.query(Career).filter(Career.id == data.target_career_id).first()
    if not career:
        raise HTTPException(status_code=400, detail="Target career not found.")
        
    user = User(
        name=data.name, 
        email=f"learner_{int(os.urandom(3).hex(), 16)}@edupath-temp.edu",
        target_career_id=data.target_career_id,
        is_email_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    career_skills = db.query(CareerSkill).filter(CareerSkill.career_id == data.target_career_id).all()
    for cs in career_skills:
        ks = KnowledgeState(user_id=user.id, skill_id=cs.skill_id, mastery=0.0)
        db.add(ks)
    db.commit()
    
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
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    answers = submission.answers
    if not answers:
        return {"status": "success", "message": "No answers submitted. Initialized mastery to 0.0"}
        
    skill_results = {}
    for ans in answers:
        q = db.query(Question).filter(Question.id == ans.question_id).first()
        if not q:
            continue
        if q.skill_id not in skill_results:
            skill_results[q.skill_id] = {"correct": 0, "total": 0}
            
        skill_results[q.skill_id]["total"] += 1
        if ans.selected_option.upper() == q.correct_option.upper():
            skill_results[q.skill_id]["correct"] += 1
            
    for skill_id, stats in skill_results.items():
        score = stats["correct"] / stats["total"] if stats["total"] > 0 else 0.0
        ks = db.query(KnowledgeState).filter(
            KnowledgeState.user_id == user_id,
            KnowledgeState.skill_id == skill_id
        ).first()
        if ks:
            ks.mastery = round(score * 0.9, 2)
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

# ================= DASHBOARD & NBLA OPTIMIZER =================

@app.get("/api/dashboard", response_model=DashboardResponse)
def get_user_dashboard(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return _build_dashboard(user.id, db)

@app.get("/api/users/{user_id}/dashboard", response_model=DashboardResponse)
def get_dashboard_by_id(user_id: int, db: Session = Depends(get_db)):
    return _build_dashboard(user_id, db)

def _build_dashboard(user_id: int, db: Session) -> DashboardResponse:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    if not user.target_career_id:
        # Default to first career
        c = db.query(Career).first()
        user.target_career_id = c.id if c else None
        db.commit()

    career = db.query(Career).filter(Career.id == user.target_career_id).first()
    career_name = career.name if career else "General AI & Engineering"

    career_skills = db.query(CareerSkill).filter(CareerSkill.career_id == user.target_career_id).all() if user.target_career_id else []
    ks_records = db.query(KnowledgeState).filter(KnowledgeState.user_id == user_id).all()
    ks_map = {ks.skill_id: ks.mastery for ks in ks_records}
    
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
            category=cs.skill.category,
            mastery=curr_mastery,
            required_mastery=req_mastery,
            importance=importance
        ))
        
    career_readiness = sum_weighted_min / sum_weighted_req if sum_weighted_req > 0.0 else 0.0
    career_readiness = round(career_readiness, 2)

    # NBLA
    next_best_action = None
    if user.target_career_id:
        nbla_result = get_next_best_learning_action(db, user_id, user.target_career_id)
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

    # Count completed modules
    total_mods = db.query(LearningModule).filter(LearningModule.career_id == user.target_career_id).count() if user.target_career_id else 0
    completed_mods = 0
    if user.target_career_id:
        mods = db.query(LearningModule).filter(LearningModule.career_id == user.target_career_id).all()
        for m in mods:
            if ks_map.get(m.skill_id, 0.0) >= 0.7:
                completed_mods += 1

    return DashboardResponse(
        career_readiness=career_readiness,
        career_name=career_name,
        study_streak_days=user.study_streak_days,
        total_study_minutes=user.total_study_minutes,
        completed_modules_count=completed_mods,
        total_modules_count=total_mods,
        skills_states=skills_states,
        next_best_action=next_best_action
    )

@app.post("/api/users/{user_id}/actions/{action_id}/complete")
def complete_action(
    user_id: int, 
    action_id: int, 
    req: ActionCompleteRequest = ActionCompleteRequest(), 
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    action = db.query(LearningAction).filter(LearningAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Learning action not found.")
        
    log = UserActionLog(user_id=user_id, action_id=action_id, performance_score=req.performance_score)
    db.add(log)
    
    ks = db.query(KnowledgeState).filter(
        KnowledgeState.user_id == user_id,
        KnowledgeState.skill_id == action.skill_id
    ).first()
    
    if not ks:
        ks = KnowledgeState(user_id=user_id, skill_id=action.skill_id, mastery=0.0)
        db.add(ks)
        
    gain = action.expected_gain
    if action.action_type == "ASSESSMENT" and req.performance_score is not None:
        ks.mastery = round(req.performance_score, 2)
    else:
        ks.mastery = min(1.0, round(ks.mastery + gain, 2))
        
    user.total_study_minutes += int(action.learning_effort)
    db.commit()
    return _build_dashboard(user_id=user_id, db=db)

# ================= PAYMENTS & SUBSCRIPTIONS =================

@app.get("/api/payments/plans", response_model=List[PlanResponse])
def list_plans(db: Session = Depends(get_db)):
    return get_plans(db)

@app.post("/api/payments/order", response_model=OrderResponse)
def create_subscription_order(
    req: CreateOrderRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return create_razorpay_order(db, user, req.plan_code)

@app.post("/api/payments/verify")
def verify_payment_order(
    req: VerifyPaymentRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return verify_razorpay_payment(db, user, req)
