from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    target_career_id = Column(Integer, ForeignKey("careers.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    career = relationship("Career")
    knowledge_states = relationship("KnowledgeState", back_populates="user", cascade="all, delete-orphan")
    action_logs = relationship("UserActionLog", back_populates="user", cascade="all, delete-orphan")


class Career(Base):
    __tablename__ = "careers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)

    skills = relationship("CareerSkill", back_populates="career")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)

    # Relationships
    careers = relationship("CareerSkill", back_populates="skill")
    actions = relationship("LearningAction", back_populates="skill")
    questions = relationship("Question", back_populates="skill")


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


class KnowledgeState(Base):
    __tablename__ = "knowledge_states"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), primary_key=True)
    mastery = Column(Float, default=0.0)  # Range 0.0 to 1.0
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="knowledge_states")
    skill = relationship("Skill")


class LearningAction(Base):
    __tablename__ = "learning_actions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
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
    performance_score = Column(Float, nullable=True)  # score between 0.0 and 1.0 for assessments/projects

    user = relationship("User", back_populates="action_logs")
    action = relationship("LearningAction", back_populates="logs")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    text = Column(String, nullable=False)
    option_a = Column(String, nullable=False)
    option_b = Column(String, nullable=False)
    option_c = Column(String, nullable=False)
    option_d = Column(String, nullable=False)
    correct_option = Column(String, nullable=False)  # A, B, C, or D

    skill = relationship("Skill", back_populates="questions")
