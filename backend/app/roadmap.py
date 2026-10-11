from sqlalchemy.orm import Session
from typing import List, Optional
from .models import (
    User, Career, LearningModule, LearningResource, 
    KnowledgeState, CareerSkill, ModuleAssessment, AssessmentAttempt,
    UserResourceProgress, Prerequisite
)
from .schemas import RoadmapResponse, RoadmapModuleResponse, LearningResourceResponse

def get_learner_roadmap(db: Session, user: User) -> Optional[RoadmapResponse]:
    """
    Generates a personalized adaptive learning roadmap respecting skill prerequisites,
    module sequence order, and current assessment evidence.
    """
    if not user.target_career_id:
        return None

    career = db.query(Career).filter(Career.id == user.target_career_id).first()
    if not career:
        return None

    modules = db.query(LearningModule).filter(
        LearningModule.career_id == career.id
    ).order_by(LearningModule.order_index).all()

    # User knowledge states mapping: skill_id -> mastery
    ks_records = db.query(KnowledgeState).filter(KnowledgeState.user_id == user.id).all()
    mastery_map = {ks.skill_id: ks.mastery for ks in ks_records}

    # Career skill targets: skill_id -> required_mastery
    cs_records = db.query(CareerSkill).filter(CareerSkill.career_id == career.id).all()
    target_map = {cs.skill_id: cs.required_mastery for cs in cs_records}

    # Prerequisite DAG mapping: child_id -> list of parent_ids
    prereqs = db.query(Prerequisite).all()
    prereq_parents = {}
    for p in prereqs:
        if p.child_skill_id not in prereq_parents:
            prereq_parents[p.child_skill_id] = []
        prereq_parents[p.child_skill_id].append(p.parent_skill_id)

    # Check passed assessments: assessment_id -> boolean
    attempts = db.query(AssessmentAttempt).filter(
        AssessmentAttempt.user_id == user.id,
        AssessmentAttempt.passed == True
    ).all()
    passed_assessment_ids = set([att.assessment_id for att in attempts])

    # Check user resource status: resource_id -> status
    user_res_progress = db.query(UserResourceProgress).filter(
        UserResourceProgress.user_id == user.id
    ).all()
    resource_status_map = {rp.resource_id: rp.status for rp in user_res_progress}

    module_responses = []
    completed_count = 0
    total_minutes = 0

    for idx, mod in enumerate(modules):
        total_minutes += mod.estimated_duration_minutes
        curr_m = mastery_map.get(mod.skill_id, 0.0)
        target_m = target_map.get(mod.skill_id, 0.8)

        # Check if assessment passed
        has_passed_exam = False
        if mod.assessment and mod.assessment.id in passed_assessment_ids:
            has_passed_exam = True

        # Check prerequisite skill constraints
        parents = prereq_parents.get(mod.skill_id, [])
        parents_satisfied = all([mastery_map.get(pid, 0.0) >= 0.5 for pid in parents])

        # Determine status
        if has_passed_exam or curr_m >= target_m:
            status = "completed"
            completed_count += 1
        elif idx == 0 or parents_satisfied:
            status = "available"
        else:
            status = "locked"

        # Load verified resources with user progress
        resources = []
        for r in mod.resources:
            resources.append(LearningResourceResponse(
                id=r.id,
                title=r.title,
                platform=r.platform,
                url=r.url,
                resource_type=r.resource_type,
                estimated_duration_minutes=r.estimated_duration_minutes,
                is_free=r.is_free,
                difficulty=r.difficulty,
                relevance_reason=r.relevance_reason,
                user_status=resource_status_map.get(r.id, "not_started")
            ))

        module_responses.append(RoadmapModuleResponse(
            id=mod.id,
            order_index=mod.order_index,
            title=mod.title,
            description=mod.description,
            skill_name=mod.skill.name,
            estimated_duration_minutes=mod.estimated_duration_minutes,
            is_core=mod.is_core,
            status=status,
            current_mastery=curr_m,
            target_mastery=target_m,
            resources=resources,
            has_passed_exam=has_passed_exam
        ))

    return RoadmapResponse(
        career_name=career.name,
        total_modules=len(modules),
        completed_modules=completed_count,
        estimated_total_hours=round(total_minutes / 60.0, 1),
        modules=module_responses
    )
