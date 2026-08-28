from sqlalchemy.orm import Session
from typing import List, Dict, Tuple, Optional
from .models import Skill, CareerSkill, Prerequisite, KnowledgeState, LearningAction
from .database import get_db

def get_descendants_and_weights(skill_id: int, adj_list: Dict[int, List[int]], visited = None) -> Dict[int, float]:
    """
    Returns a dictionary of all descendant skill IDs reachable from skill_id, 
    mapping to their dependency strength w(skill_id, desc_id).
    Decays strength with distance (0.5^distance).
    """
    if visited is None:
        visited = {}
    
    # We want to traverse descendants. The adj_list should map parent -> children.
    # We do a BFS or DFS to find all reachable children.
    queue = [(skill_id, 1.0)]  # (current_id, current_weight)
    descendants = {}
    
    while queue:
        curr, weight = queue.pop(0)
        if curr != skill_id:
            if curr not in descendants or weight > descendants[curr]:
                descendants[curr] = weight
        
        children = adj_list.get(curr, [])
        for child in children:
            child_weight = weight * 0.5  # Decay weight for multi-step dependencies
            if child not in visited or child_weight > visited.get(child, 0.0):
                visited[child] = child_weight
                queue.append((child, child_weight))
                
    return descendants

def calculate_prerequisite_values(
    db: Session, 
    career_id: int, 
    knowledge_states: Dict[int, float]
) -> Dict[int, float]:
    """
    Computes P_val(s) = sum_{d in desc(s)} w(s, d) * I_c(d)
    for all skills. We only sum over descendant skills d that have a non-zero skill gap
    (i.e., the user still needs to learn them).
    """
    # 1. Get all prerequisites
    prereqs = db.query(Prerequisite).all()
    # Build adjacency list: parent -> list of children
    adj_list = {}
    for p in prereqs:
        if p.parent_skill_id not in adj_list:
            adj_list[p.parent_skill_id] = []
        adj_list[p.parent_skill_id].append(p.child_skill_id)
        
    # 2. Get career skill importances
    career_skills = db.query(CareerSkill).filter(CareerSkill.career_id == career_id).all()
    career_importances = {cs.skill_id: cs.importance for cs in career_skills}
    career_required = {cs.skill_id: cs.required_mastery for cs in career_skills}
    
    # 3. Compute gaps
    unmet_descendants = {}
    for skill_id, req_mastery in career_required.items():
        curr_mastery = knowledge_states.get(skill_id, 0.0)
        gap = max(0.0, req_mastery - curr_mastery)
        if gap > 0.05:  # Skill is not yet mastered
            unmet_descendants[skill_id] = career_importances.get(skill_id, 0.5)

    # 4. Compute P_val for each skill
    all_skills = db.query(Skill).all()
    prereq_values = {}
    
    for s in all_skills:
        descendants = get_descendants_and_weights(s.id, adj_list)
        p_val = 0.0
        for desc_id, weight in descendants.items():
            if desc_id in unmet_descendants:
                # Add weighted importance of the unmet descendant
                p_val += weight * unmet_descendants[desc_id]
        prereq_values[s.id] = p_val
        
    return prereq_values

def get_next_best_learning_action(
    db: Session,
    user_id: int,
    career_id: int,
    alpha: float = 1.5,   # Weight for Skill Gap
    beta: float = 1.0,    # Weight for Career Importance
    gamma: float = 1.2,   # Weight for Prerequisite Value
    delta: float = 0.8,   # Weight for Expected Gain
    lambda_param: float = 0.5  # Penalty for Effort
) -> Optional[Tuple[LearningAction, float, Dict[str, float], str]]:
    """
    Selects the NBLA using the multi-factor scoring function.
    Returns: (SelectedAction, ActionScore, ScoreComponents, ExplanationString)
    """
    # 1. Fetch user knowledge states
    ks_records = db.query(KnowledgeState).filter(KnowledgeState.user_id == user_id).all()
    knowledge_states = {ks.skill_id: ks.mastery for ks in ks_records}
    
    # 2. Fetch career requirements
    career_skills = db.query(CareerSkill).filter(CareerSkill.career_id == career_id).all()
    if not career_skills:
        return None
        
    career_importances = {cs.skill_id: cs.importance for cs in career_skills}
    career_required = {cs.skill_id: cs.required_mastery for cs in career_skills}
    
    # 3. Fetch all prerequisites to filter out actions with unmet prerequisites
    prereqs = db.query(Prerequisite).all()
    # Map child -> list of parent prerequisites
    prereq_map = {}
    for p in prereqs:
        if p.child_skill_id not in prereq_map:
            prereq_map[p.child_skill_id] = []
        prereq_map[p.child_skill_id].append(p.parent_skill_id)
        
    # Check if a skill has critical unmet prerequisites (mastery < 0.5)
    def has_unmet_prerequisites(skill_id: int) -> bool:
        parents = prereq_map.get(skill_id, [])
        for parent_id in parents:
            parent_mastery = knowledge_states.get(parent_id, 0.0)
            if parent_mastery < 0.5:  # Threshold for "unmet prerequisite"
                return True
        return False

    # 4. Calculate Prerequisite Values
    prereq_values = calculate_prerequisite_values(db, career_id, knowledge_states)
    
    # 5. Fetch all candidate actions targeting skills in this career
    candidate_actions = db.query(LearningAction).filter(
        LearningAction.skill_id.in_(career_importances.keys())
    ).all()
    
    scored_actions = []
    
    # Find max effort to normalize effort penalty
    max_effort = max([a.learning_effort for a in candidate_actions]) if candidate_actions else 60.0
    
    for action in candidate_actions:
        skill_id = action.skill_id
        curr_mastery = knowledge_states.get(skill_id, 0.0)
        req_mastery = career_required.get(skill_id, 0.8)
        
        # Calculate Skill Gap
        gap = max(0.0, req_mastery - curr_mastery)
        
        # If the user has already mastered this skill, skip it
        if gap <= 0.05:
            continue
            
        # Check for critical unmet prerequisites
        # EXCEPTION: If the action itself is to help learn the unmet prerequisite, we allow it.
        # But if the action is for an advanced skill whose prerequisites are not met, we filter it out.
        if has_unmet_prerequisites(skill_id):
            continue
            
        # Get components
        importance = career_importances.get(skill_id, 0.0)
        p_val = prereq_values.get(skill_id, 0.0)
        gain = action.expected_gain
        effort = action.learning_effort
        
        # Normalize terms to [0, 1] range for fair comparison
        norm_gap = gap  # Already [0, 1]
        norm_importance = importance  # Already [0, 1]
        
        # Normalize prerequisite value
        max_pval = max(prereq_values.values()) if prereq_values.values() else 1.0
        norm_pval = p_val / max_pval if max_pval > 0 else 0.0
        
        # Normalize effort
        norm_effort = effort / max_effort if max_effort > 0 else 0.0
        norm_gain = gain  # Already [0, 1]
        
        # NBLA Scoring formula
        gap_score = alpha * norm_gap
        imp_score = beta * norm_importance
        pre_score = gamma * norm_pval
        gain_score = delta * norm_gain
        eff_penalty = lambda_param * norm_effort
        
        total_score = gap_score + imp_score + pre_score + gain_score - eff_penalty
        
        components = {
            "gap_contribution": round(gap_score, 3),
            "importance_contribution": round(imp_score, 3),
            "prerequisite_contribution": round(pre_score, 3),
            "gain_contribution": round(gain_score, 3),
            "effort_penalty": round(-eff_penalty, 3)
        }
        
        scored_actions.append((action, total_score, components))
        
    if not scored_actions:
        return None
        
    # Sort actions by score descending
    scored_actions.sort(key=lambda x: x[1], reverse=True)
    best_action, best_score, best_components = scored_actions[0]
    
    # 6. Generate explainability description
    skill_name = best_action.skill.name
    action_type = best_action.action_type.lower()
    
    # Find dominant positive factors
    pos_factors = [
        ("gap_contribution", "it addresses your current skill gap"),
        ("importance_contribution", "it is highly critical for your target career role"),
        ("prerequisite_contribution", "it unlocks multiple advanced dependent topics down the path"),
        ("gain_contribution", "it provides high expected learning gains")
    ]
    sorted_pos = sorted(
        [(k, v, best_components[k]) for k, v in pos_factors], 
        key=lambda x: x[2], 
        reverse=True
    )
    
    dominant_reasons = [reason for _, reason, val in sorted_pos[:2] if val > 0.3]
    reasons_str = " and ".join(dominant_reasons)
    if not reasons_str:
        reasons_str = "it provides the best overall path efficiency"
        
    explanation = (
        f"\"{best_action.title}\" is recommended as your Next Best Learning Action because {reasons_str}. "
        f"It targets \"{skill_name}\" which has a required career mastery of {int(career_required[skill_id]*100)}% "
        f"(your current mastery is {int(knowledge_states.get(skill_id, 0.0)*100)}%). "
        f"This {action_type} activity will take approximately {int(best_action.learning_effort)} minutes "
        f"with an expected mastery increase of +{int(best_action.expected_gain*100)}%."
    )
    
    return best_action, best_score, best_components, explanation
