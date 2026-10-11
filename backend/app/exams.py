from fastapi import HTTPException
from sqlalchemy.orm import Session
import json
import random
from typing import List
from .models import User, LearningModule, ModuleAssessment, Question, AssessmentAttempt, KnowledgeState, CareerSkill
from .schemas import (
    ExamStartResponse, ExamQuestionItem, ExamSubmissionRequest, 
    ExamResultResponse, ExamReviewItem
)
from .email_service import send_exam_result_email

def start_module_exam(db: Session, module_id: int) -> ExamStartResponse:
    """
    Delivers a secure, randomized examination for the learning module.
    Correct answers and explanations are strictly omitted to prevent cheating.
    """
    module = db.query(LearningModule).filter(LearningModule.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found.")

    assessment = module.assessment
    if not assessment:
        # Fallback: create assessment if missing
        assessment = ModuleAssessment(
            module_id=module.id,
            title=f"{module.title} Assessment",
            duration_minutes=15,
            pass_percentage=70.0
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)

    questions = db.query(Question).filter(
        (Question.assessment_id == assessment.id) | (Question.skill_id == module.skill_id)
    ).all()

    if not questions:
        raise HTTPException(status_code=400, detail="No assessment questions configured for this module yet.")

    # Randomize question order
    shuffled_questions = list(questions)
    random.shuffle(shuffled_questions)

    question_items = [
        ExamQuestionItem(
            id=q.id,
            text=q.text,
            option_a=q.option_a,
            option_b=q.option_b,
            option_c=q.option_c,
            option_d=q.option_d
        )
        for q in shuffled_questions[:10]  # Standard 10 questions per exam
    ]

    return ExamStartResponse(
        assessment_id=assessment.id,
        module_title=module.title,
        duration_minutes=assessment.duration_minutes,
        pass_percentage=assessment.pass_percentage,
        questions=question_items
    )

def evaluate_module_exam(
    db: Session,
    user: User,
    module_id: int,
    submission: ExamSubmissionRequest
) -> ExamResultResponse:
    """
    Evaluates submitted answers, computes pass/fail status, creates attempt record,
    updates skill knowledge state, and returns comprehensive answer explanations.
    """
    module = db.query(LearningModule).filter(LearningModule.id == module_id).first()
    if not module or not module.assessment:
        raise HTTPException(status_code=404, detail="Module assessment not found.")

    assessment = module.assessment
    answers = submission.answers

    # Map questions for grading
    q_ids = [a.question_id for a in answers]
    db_questions = db.query(Question).filter(Question.id.in_(q_ids)).all()
    q_map = {q.id: q for q in db_questions}

    correct_count = 0
    total_count = len(answers)
    reviews: List[ExamReviewItem] = []

    for ans in answers:
        q = q_map.get(ans.question_id)
        if not q:
            continue
        is_corr = (ans.selected_option.strip().upper() == q.correct_option.strip().upper())
        if is_corr:
            correct_count += 1
        reviews.append(ExamReviewItem(
            question_id=q.id,
            text=q.text,
            user_selected=ans.selected_option.strip().upper(),
            correct_option=q.correct_option.strip().upper(),
            is_correct=is_corr,
            explanation=q.explanation or "Mastering this concept is essential for the module."
        ))

    score_pct = round((correct_count / total_count * 100.0) if total_count > 0 else 0.0, 1)
    passed = (score_pct >= assessment.pass_percentage)

    # Count prior attempts
    prior_attempts = db.query(AssessmentAttempt).filter(
        AssessmentAttempt.user_id == user.id,
        AssessmentAttempt.assessment_id == assessment.id
    ).count()

    attempt = AssessmentAttempt(
        user_id=user.id,
        assessment_id=assessment.id,
        score_percentage=score_pct,
        passed=passed,
        attempt_number=prior_attempts + 1,
        answers_json=json.dumps([{ "q_id": a.question_id, "opt": a.selected_option } for a in answers])
    )
    db.add(attempt)

    # Update knowledge state for the skill
    ks = db.query(KnowledgeState).filter(
        KnowledgeState.user_id == user.id,
        KnowledgeState.skill_id == module.skill_id
    ).first()
    if not ks:
        ks = KnowledgeState(user_id=user.id, skill_id=module.skill_id, mastery=0.0)
        db.add(ks)

    score_ratio = score_pct / 100.0
    if passed:
        # Increase mastery using Bayesian-inspired update
        ks.mastery = min(1.0, round(max(ks.mastery, 0.7 + (score_ratio - 0.7) * 0.8), 2))
    else:
        # Slightly update knowledge with score evidence
        ks.mastery = round(max(ks.mastery, score_ratio * 0.5), 2)

    ks.assessment_count = (ks.assessment_count or 0) + 1
    user.study_streak_days = max(user.study_streak_days, 1)
    user.total_study_minutes += assessment.duration_minutes
    db.commit()

    # Trigger transactional email notification
    send_exam_result_email(
        db=db,
        user_id=user.id,
        email=user.email,
        module_title=module.title,
        score=score_pct,
        passed=passed
    )

    feedback = (
        f"Congratulations! You passed the {module.title} assessment with {score_pct}%. Dependent modules are now unlocked."
        if passed else
        f"You scored {score_pct}% (Pass threshold: {int(assessment.pass_percentage)}%). Please review the practice resources below and try again."
    )

    return ExamResultResponse(
        assessment_id=assessment.id,
        score_percentage=score_pct,
        passed=passed,
        pass_threshold=assessment.pass_percentage,
        total_questions=total_count,
        correct_count=correct_count,
        new_skill_mastery=ks.mastery,
        answer_reviews=reviews,
        feedback_message=feedback
    )
