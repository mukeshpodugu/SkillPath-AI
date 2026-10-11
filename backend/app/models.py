from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)
    role = Column(String, default="student")  # "student" | "admin"
    is_email_verified = Column(Boolean, default=False)
    target_career_id = Column(Integer, ForeignKey("careers.id"), nullable=True)
    subscription_tier = Column(String, default="free")  # "free" | "premium_monthly" | "premium_annual"
    subscription_expires_at = Column(DateTime, nullable=True)
    study_streak_days = Column(Integer, default=1)
    total_study_minutes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    career = relationship("Career")
    profile = relationship("LearnerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    knowledge_states = relationship("KnowledgeState", back_populates="user", cascade="all, delete-orphan")
    action_logs = relationship("UserActionLog", back_populates="user", cascade="all, delete-orphan")
    resource_progress = relationship("UserResourceProgress", back_populates="user", cascade="all, delete-orphan")
    assessment_attempts = relationship("AssessmentAttempt", back_populates="user", cascade="all, delete-orphan")
    payment_orders = relationship("PaymentOrder", back_populates="user", cascade="all, delete-orphan")


class LearnerProfile(Base):
    __tablename__ = "learner_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    education_level = Column(String, default="B.Tech Computer Science")
    degree_major = Column(String, default="Computer Science & Engineering")
    current_status = Column(String, default="Student")  # Student, Job Seeker, Professional
    technical_skills = Column(Text, default="Python, Git")
    soft_skills = Column(Text, default="Problem Solving, Communication")
    certifications = Column(Text, default="")
    projects_summary = Column(Text, default="")
    work_experience_years = Column(Float, default=0.0)
    study_hours_per_week = Column(Integer, default=10)
    preferred_format = Column(String, default="Interactive & Videos")  # Videos, Interactive, Reading, Projects
    resume_filename = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="profile")


class Career(Base):
    __tablename__ = "careers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    onet_soc_code = Column(String, nullable=True)
    typical_salary_range = Column(String, default="₹8,00,000 - ₹24,00,000 / yr")
    market_growth_rate = Column(String, default="+22% (High Demand)")

    skills = relationship("CareerSkill", back_populates="career")
    modules = relationship("LearningModule", back_populates="career", cascade="all, delete-orphan")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, default="General")  # Programming, Mathematics, AI/ML, Frontend, DevOps
    description = Column(Text, nullable=True)

    careers = relationship("CareerSkill", back_populates="skill")
    actions = relationship("LearningAction", back_populates="skill")
    questions = relationship("Question", back_populates="skill")
    modules = relationship("LearningModule", back_populates="skill")


class CareerSkill(Base):
    __tablename__ = "career_skills"

    career_id = Column(Integer, ForeignKey("careers.id"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), primary_key=True)
    required_mastery = Column(Float, default=0.8)
    importance = Column(Float, default=0.5)  # Range 0.0 to 1.0

    career = relationship("Career", back_populates="skills")
    skill = relationship("Skill", back_populates="careers")


class Prerequisite(Base):
    __tablename__ = "prerequisites"

    parent_skill_id = Column(Integer, ForeignKey("skills.id"), primary_key=True)
    child_skill_id = Column(Integer, ForeignKey("skills.id"), primary_key=True)
    dependency_type = Column(String, default="STRICT")  # STRICT, RECOMMENDED


class KnowledgeState(Base):
    __tablename__ = "knowledge_states"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), primary_key=True)
    mastery = Column(Float, default=0.0)  # Range 0.0 to 1.0
    assessment_count = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="knowledge_states")
    skill = relationship("Skill")


class LearningModule(Base):
    __tablename__ = "learning_modules"

    id = Column(Integer, primary_key=True, index=True)
    career_id = Column(Integer, ForeignKey("careers.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=1)
    estimated_duration_minutes = Column(Integer, default=120)
    is_core = Column(Boolean, default=True)

    career = relationship("Career", back_populates="modules")
    skill = relationship("Skill", back_populates="modules")
    resources = relationship("LearningResource", back_populates="module", cascade="all, delete-orphan")
    assessment = relationship("ModuleAssessment", back_populates="module", uselist=False, cascade="all, delete-orphan")


class LearningResource(Base):
    __tablename__ = "learning_resources"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("learning_modules.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    title = Column(String, nullable=False)
    platform = Column(String, nullable=False)  # YouTube, Coursera, freeCodeCamp, Kaggle, MDN, W3Schools, GeeksforGeeks
    url = Column(String, nullable=False)
    resource_type = Column(String, default="Video Tutorial")  # Video Tutorial, Official Documentation, Interactive Course, Practice Lab
    estimated_duration_minutes = Column(Integer, default=45)
    is_free = Column(Boolean, default=True)
    difficulty = Column(String, default="Beginner")  # Beginner, Intermediate, Advanced
    relevance_reason = Column(Text, nullable=True)

    module = relationship("LearningModule", back_populates="resources")


class UserResourceProgress(Base):
    __tablename__ = "user_resource_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resource_id = Column(Integer, ForeignKey("learning_resources.id"), nullable=False)
    status = Column(String, default="not_started")  # not_started, started, completed
    minutes_spent = Column(Integer, default=0)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="resource_progress")
    resource = relationship("LearningResource")


class ModuleAssessment(Base):
    __tablename__ = "module_assessments"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("learning_modules.id"), unique=True, nullable=False)
    title = Column(String, nullable=False)
    duration_minutes = Column(Integer, default=15)
    pass_percentage = Column(Float, default=70.0)
    max_attempts = Column(Integer, default=5)

    module = relationship("LearningModule", back_populates="assessment")
    questions = relationship("Question", back_populates="assessment", cascade="all, delete-orphan")
    attempts = relationship("AssessmentAttempt", back_populates="assessment", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("module_assessments.id"), nullable=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    text = Column(Text, nullable=False)
    option_a = Column(String, nullable=False)
    option_b = Column(String, nullable=False)
    option_c = Column(String, nullable=False)
    option_d = Column(String, nullable=False)
    correct_option = Column(String, nullable=False)  # A, B, C, or D
    explanation = Column(Text, default="Review the core concepts for this question.")

    assessment = relationship("ModuleAssessment", back_populates="questions")
    skill = relationship("Skill", back_populates="questions")


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assessment_id = Column(Integer, ForeignKey("module_assessments.id"), nullable=False)
    score_percentage = Column(Float, nullable=False)
    passed = Column(Boolean, nullable=False)
    attempt_number = Column(Integer, default=1)
    answers_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="assessment_attempts")
    assessment = relationship("ModuleAssessment", back_populates="attempts")


class LearningAction(Base):
    __tablename__ = "learning_actions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    action_type = Column(String, nullable=False)  # LEARN, PRACTICE, ASSESSMENT, MINI_PROJECT, PROJECT, REVIEW
    expected_gain = Column(Float, default=0.1)
    learning_effort = Column(Float, default=30.0)  # in minutes
    url = Column(String, nullable=True)

    skill = relationship("Skill", back_populates="actions")
    logs = relationship("UserActionLog", back_populates="action")


class UserActionLog(Base):
    __tablename__ = "user_action_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action_id = Column(Integer, ForeignKey("learning_actions.id"), nullable=False)
    completed_at = Column(DateTime, default=datetime.datetime.utcnow)
    performance_score = Column(Float, nullable=True)

    user = relationship("User", back_populates="action_logs")
    action = relationship("LearningAction", back_populates="logs")


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False)  # free, premium_monthly, premium_annual
    name = Column(String, nullable=False)
    price_inr = Column(Integer, default=0)
    billing_interval = Column(String, default="month")  # month, year, lifetime
    features_json = Column(Text, default="[]")


class PaymentOrder(Base):
    __tablename__ = "payment_orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_code = Column(String, nullable=False)
    amount_inr = Column(Integer, nullable=False)
    razorpay_order_id = Column(String, unique=True, index=True, nullable=False)
    razorpay_payment_id = Column(String, nullable=True)
    status = Column(String, default="created")  # created, paid, failed, refunded
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="payment_orders")


class EmailNotificationLog(Base):
    __tablename__ = "email_notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    recipient_email = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    template_name = Column(String, nullable=False)
    status = Column(String, default="sent")  # sent, logged_sandbox, failed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ResearchEvaluationRecord(Base):
    __tablename__ = "research_evaluation_records"

    id = Column(Integer, primary_key=True, index=True)
    baseline_name = Column(String, nullable=False)
    precision_k = Column(Float, default=0.0)
    ndcg_k = Column(Float, default=0.0)
    skill_gap_reduction = Column(Float, default=0.0)
    prerequisite_violations = Column(Float, default=0.0)
    learning_efficiency = Column(Float, default=0.0)
    career_readiness_gain = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
