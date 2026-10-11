from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

# ================= AUTH & USER SCHEMAS =================
class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    role: Optional[str] = "student"

class UserLogin(BaseModel):
    email: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    email: str
    new_password: str

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    education_level: Optional[str] = None
    degree_major: Optional[str] = None
    current_status: Optional[str] = None
    technical_skills: Optional[str] = None
    soft_skills: Optional[str] = None
    certifications: Optional[str] = None
    projects_summary: Optional[str] = None
    work_experience_years: Optional[float] = None
    study_hours_per_week: Optional[int] = None
    preferred_format: Optional[str] = None

class LearnerProfileResponse(BaseModel):
    education_level: Optional[str] = None
    degree_major: Optional[str] = None
    current_status: Optional[str] = None
    technical_skills: Optional[str] = None
    soft_skills: Optional[str] = None
    certifications: Optional[str] = None
    projects_summary: Optional[str] = None
    work_experience_years: Optional[float] = None
    study_hours_per_week: Optional[int] = None
    preferred_format: Optional[str] = None
    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_email_verified: bool
    target_career_id: Optional[int] = None
    subscription_tier: str
    study_streak_days: int
    total_study_minutes: int
    profile: Optional[LearnerProfileResponse] = None
    created_at: datetime
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# ================= CAREER & RECOMMENDER SCHEMAS =================
class SkillResponse(BaseModel):
    id: int
    name: str
    category: str
    description: Optional[str] = None
    class Config:
        from_attributes = True

class CareerSkillDetail(BaseModel):
    skill_id: int
    skill_name: str
    category: str
    required_mastery: float
    importance: float

class CareerResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    onet_soc_code: Optional[str] = None
    typical_salary_range: Optional[str] = None
    market_growth_rate: Optional[str] = None
    skills: Optional[List[CareerSkillDetail]] = None
    class Config:
        from_attributes = True

class CareerRecommendationItem(BaseModel):
    career: CareerResponse
    compatibility_score: float  # 0 to 100%
    matched_skills: List[str]
    missing_or_weak_skills: List[str]
    match_rationale: str

# ================= ROADMAP & LEARNING RESOURCE SCHEMAS =================
class LearningResourceResponse(BaseModel):
    id: int
    title: str
    platform: str
    url: str
    resource_type: str
    estimated_duration_minutes: int
    is_free: bool
    difficulty: str
    relevance_reason: Optional[str] = None
    user_status: Optional[str] = "not_started"
    class Config:
        from_attributes = True

class ResourceStatusUpdate(BaseModel):
    status: str  # not_started, started, completed
    minutes_spent: Optional[int] = 0

class RoadmapModuleResponse(BaseModel):
    id: int
    order_index: int
    title: str
    description: Optional[str] = None
    skill_name: str
    estimated_duration_minutes: int
    is_core: bool
    status: str  # locked, available, completed
    current_mastery: float
    target_mastery: float
    resources: List[LearningResourceResponse]
    has_passed_exam: bool
    class Config:
        from_attributes = True

class RoadmapResponse(BaseModel):
    career_name: str
    total_modules: int
    completed_modules: int
    estimated_total_hours: float
    modules: List[RoadmapModuleResponse]

# ================= EXAMS & ASSESSMENTS SCHEMAS =================
class ExamQuestionItem(BaseModel):
    id: int
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    # Notice: correct_option is deliberately OMITTED here for exam security

class ExamStartResponse(BaseModel):
    assessment_id: int
    module_title: str
    duration_minutes: int
    pass_percentage: float
    questions: List[ExamQuestionItem]

class ExamAnswerSubmission(BaseModel):
    question_id: int
    selected_option: str  # A, B, C, D

class ExamSubmissionRequest(BaseModel):
    answers: List[ExamAnswerSubmission]

class ExamReviewItem(BaseModel):
    question_id: int
    text: str
    user_selected: str
    correct_option: str
    is_correct: bool
    explanation: str

class ExamResultResponse(BaseModel):
    assessment_id: int
    score_percentage: float
    passed: bool
    pass_threshold: float
    total_questions: int
    correct_count: int
    new_skill_mastery: float
    answer_reviews: List[ExamReviewItem]
    feedback_message: str

# ================= NBLA & DASHBOARD SCHEMAS =================
class LearningActionResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    skill_id: int
    skill_name: str
    action_type: str
    expected_gain: float
    learning_effort: float
    url: Optional[str] = None
    class Config:
        from_attributes = True

class NBLAExplanation(BaseModel):
    summary: str
    components: Dict[str, float]

class NBLARecommendationResponse(BaseModel):
    action: LearningActionResponse
    action_score: float
    explanation: NBLAExplanation

class KnowledgeStateResponse(BaseModel):
    skill_id: int
    skill_name: str
    category: str
    mastery: float
    required_mastery: float
    importance: float
    class Config:
        from_attributes = True

class DashboardResponse(BaseModel):
    career_readiness: float
    career_name: str
    study_streak_days: int
    total_study_minutes: int
    completed_modules_count: int
    total_modules_count: int
    skills_states: List[KnowledgeStateResponse]
    next_best_action: Optional[NBLARecommendationResponse] = None

# ================= PAYMENTS & SUBSCRIPTIONS SCHEMAS =================
class PlanResponse(BaseModel):
    code: str
    name: str
    price_inr: int
    billing_interval: str
    features: List[str]

class CreateOrderRequest(BaseModel):
    plan_code: str

class OrderResponse(BaseModel):
    order_id: str
    amount_inr: int
    currency: str = "INR"
    plan_name: str
    key_id: str
    sandbox_mode: bool

class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

# ================= ADMIN SCHEMAS =================
class AdminStatsResponse(BaseModel):
    total_users: int
    total_students: int
    total_admins: int
    total_modules: int
    total_resources: int
    total_exam_attempts: int
    total_revenue_inr: int
    recent_email_count: int

# ================= RESEARCH BENCHMARKS SCHEMAS =================
class BaselineMetricItem(BaseModel):
    baseline_name: str
    precision_k: float
    ndcg_k: float
    skill_gap_reduction: float
    prerequisite_violations: float
    learning_efficiency: float
    career_readiness_gain: float
    description: str

class ResearchBenchmarkResponse(BaseModel):
    evaluated_at: str
    baselines: List[BaselineMetricItem]
    analysis_conclusion: str
