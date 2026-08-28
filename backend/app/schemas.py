from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

# Career Schemas
class CareerBase(BaseModel):
    name: str
    description: Optional[str] = None

class CareerResponse(CareerBase):
    id: int
    class Config:
        from_attributes = True

# Skill Schemas
class SkillBase(BaseModel):
    name: str
    description: Optional[str] = None

class SkillResponse(SkillBase):
    id: int
    class Config:
        from_attributes = True

# CareerSkill Schema
class CareerSkillResponse(BaseModel):
    skill: SkillResponse
    required_mastery: float
    importance: float
    class Config:
        from_attributes = True

# User Schemas
class UserCreate(BaseModel):
    name: str

class UserOnboard(BaseModel):
    name: str
    target_career_id: int
    known_skill_ids: List[int]

class UserResponse(BaseModel):
    id: int
    name: str
    target_career_id: Optional[int]
    created_at: datetime
    class Config:
        from_attributes = True

# Question Schemas (for diagnostic test)
class QuestionResponse(BaseModel):
    id: int
    skill_id: int
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    class Config:
        from_attributes = True

class SingleAnswerSubmission(BaseModel):
    question_id: int
    selected_option: str  # A, B, C, or D

class DiagnosticSubmission(BaseModel):
    answers: List[SingleAnswerSubmission]

# Learning Action Schemas
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

# Explanation Schema
class NBLAExplanation(BaseModel):
    summary: str
    components: Dict[str, float]  # Contribution of gap, importance, prereq, gain, effort

class NBLARecommendationResponse(BaseModel):
    action: LearningActionResponse
    action_score: float
    explanation: NBLAExplanation

# Knowledge State Schema
class KnowledgeStateResponse(BaseModel):
    skill_id: int
    skill_name: str
    mastery: float
    required_mastery: float
    importance: float
    class Config:
        from_attributes = True

class DashboardResponse(BaseModel):
    career_readiness: float
    career_name: str
    skills_states: List[KnowledgeStateResponse]
    next_best_action: Optional[NBLARecommendationResponse] = None

class ActionCompleteRequest(BaseModel):
    performance_score: Optional[float] = None # Optional, e.g. quiz score or project grade
