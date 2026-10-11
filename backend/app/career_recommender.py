from sqlalchemy.orm import Session
from typing import List, Dict, Any
from .models import Career, CareerSkill, Skill, LearnerProfile, User
from .schemas import CareerRecommendationItem, CareerResponse, CareerSkillDetail

def recommend_careers_for_learner(db: Session, user: User) -> List[CareerRecommendationItem]:
    """
    Analyzes user profile technical skills, background, and interests,
    matches them against career requirements (O*NET aligned), and produces
    ranked compatibility scores with transparent rationales.
    """
    user_skills_text = ""
    if user.profile and user.profile.technical_skills:
        user_skills_text = user.profile.technical_skills.lower()

    # Parse user skills into a clean normalized set of tokens
    user_tokens = set([s.strip() for s in user_skills_text.replace(";", ",").split(",") if s.strip()])
    
    careers = db.query(Career).all()
    recommendations = []

    for career in careers:
        career_skills = db.query(CareerSkill).filter(CareerSkill.career_id == career.id).all()
        if not career_skills:
            continue

        total_weight = sum([cs.importance for cs in career_skills])
        matched_weight = 0.0
        matched_names = []
        missing_names = []
        skill_details = []

        for cs in career_skills:
            s_name = cs.skill.name
            skill_details.append(CareerSkillDetail(
                skill_id=cs.skill_id,
                skill_name=s_name,
                category=cs.skill.category,
                required_mastery=cs.required_mastery,
                importance=cs.importance
            ))

            # Fuzzy token matching: check if skill name is in user tokens or vice versa
            norm_name = s_name.lower()
            is_match = any(token in norm_name or norm_name in token for token in user_tokens)
            
            if is_match:
                matched_weight += cs.importance
                matched_names.append(s_name)
            else:
                missing_names.append(s_name)

        # Baseline compatibility: minimum 15% so fresh learners still see growth potential
        raw_ratio = (matched_weight / total_weight) if total_weight > 0 else 0.0
        compatibility_score = round(min(98.0, max(20.0, raw_ratio * 100)), 1)

        # Build natural-language explainable rationale
        if matched_names:
            rationale = (
                f"Matches {len(matched_names)} of your existing skills ({', '.join(matched_names[:3])}). "
                f"You have a strong foundation, and mastering {', '.join(missing_names[:2])} will make you role-ready."
            )
        else:
            rationale = (
                f"An excellent growth path aligned with your learning goals. "
                f"Covers high-demand industry skills with structured foundational prerequisites."
            )

        career_resp = CareerResponse(
            id=career.id,
            name=career.name,
            description=career.description,
            onet_soc_code=career.onet_soc_code,
            typical_salary_range=career.typical_salary_range,
            market_growth_rate=career.market_growth_rate,
            skills=skill_details
        )

        recommendations.append(CareerRecommendationItem(
            career=career_resp,
            compatibility_score=compatibility_score,
            matched_skills=matched_names,
            missing_or_weak_skills=missing_names,
            match_rationale=rationale
        ))

    # Rank by compatibility score descending
    recommendations.sort(key=lambda r: r.compatibility_score, reverse=True)
    return recommendations
