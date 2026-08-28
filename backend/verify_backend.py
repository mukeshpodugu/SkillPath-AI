import os
import sys

# Add the current directory to sys.path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base, SessionLocal
from app.models import User, Career, Skill, CareerSkill, KnowledgeState
from app.seed import seed_data
from app.optimizer import get_next_best_learning_action

def verify():
    print("Executing backend verification script...")
    
    # 1. Create tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")
    
    # 2. Seed data
    db = SessionLocal()
    try:
        seed_data(db)
        print("Database seeded successfully.")
        
        # 3. Create test user
        # Fetch Machine Learning Engineer Career
        mle = db.query(Career).filter(Career.name == "Machine Learning Engineer").first()
        assert mle is not None, "MLE Career not found in seeded database"
        
        test_user = User(name="Test Learner", target_career_id=mle.id)
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"Created test user: {test_user.name} (ID: {test_user.id})")
        
        # Initialize knowledge states
        career_skills = db.query(CareerSkill).filter(CareerSkill.career_id == mle.id).all()
        for cs in career_skills:
            ks = KnowledgeState(user_id=test_user.id, skill_id=cs.skill_id, mastery=0.0)
            db.add(ks)
        db.commit()
        
        # 4. Trigger Optimizer (Initial recommendation)
        recommendation = get_next_best_learning_action(db, test_user.id, mle.id)
        assert recommendation is not None, "Optimizer failed to return an NBLA recommendation"
        
        action, score, components, explanation = recommendation
        print("\n--- TEST RECOMMENDATION ---")
        print(f"Recommended Action: {action.title} (Type: {action.action_type})")
        print(f"Target Skill: {action.skill.name}")
        print(f"Score: {score:.3f}")
        print(f"Explanation: {explanation}")
        print("----------------------------\n")
        
        # The recommended action should be Python, Statistics or Linear Algebra
        # because ML, Deep Learning, and MLOps have unmet prerequisites.
        assert action.skill.name in ["Python", "Statistics", "Linear Algebra"], \
            f"Expected a foundational skill action, got {action.skill.name}"
            
        print("Verification PASSED: Prerequisite ordering and NBLA computation are working correctly!")
        
    except Exception as e:
        print(f"Verification FAILED: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    verify()
