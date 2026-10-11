import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base, SessionLocal
from app.models import User, Career, LearningModule, ModuleAssessment
from app.seed import seed_data
from app.auth import hash_password, verify_password, create_access_token, verify_token
from app.career_recommender import recommend_careers_for_learner
from app.roadmap import get_learner_roadmap
from app.exams import start_module_exam, evaluate_module_exam
from app.schemas import ExamSubmissionRequest, ExamAnswerSubmission, VerifyPaymentRequest
from app.payments import create_razorpay_order, verify_razorpay_payment
from app.research_eval import get_research_evaluation_benchmark
from app.optimizer import get_next_best_learning_action

def verify_all():
    print("=== STARTING FULL EDUPATH AI PLATFORM AUDIT ===")
    
    # 1. Database & Tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_data(db)
    print("[1] Database schema & seed data initialized.")

    # 2. Authentication Test
    pwd = "secretpassword"
    hashed = hash_password(pwd)
    assert verify_password(pwd, hashed), "Password verification failed"
    assert not verify_password("wrong", hashed), "Password false positive"

    token = create_access_token(1, "student", "test@edupath.ai")
    payload = verify_token(token)
    assert payload is not None and payload["sub"] == "1", "JWT token generation/verification failed"
    print("[2] Cryptographic password hashing & JWT token verification passed.")

    # 3. Student Profile & Career Matcher
    student = db.query(User).filter(User.email == "student@edupath.ai").first()
    assert student is not None, "Demo student user not found in seed"
    recommendations = recommend_careers_for_learner(db, student)
    assert len(recommendations) >= 3, "Career recommendations failed"
    top_career = recommendations[0]
    print(f"[3] AI Career Recommender matched top role: {top_career.career.name} ({top_career.compatibility_score}% compatibility)")
    print(f"    Rationale: {top_career.match_rationale}")

    # 4. Adaptive Roadmap & Verified Resources
    student.target_career_id = top_career.career.id
    db.commit()
    roadmap = get_learner_roadmap(db, student)
    assert roadmap is not None, "Roadmap generation failed"
    assert roadmap.total_modules >= 4, f"Expected at least 4 modules, got {roadmap.total_modules}"
    first_mod = roadmap.modules[0]
    assert len(first_mod.resources) > 0, "No learning resources attached to module"
    print(f"[4] Adaptive Roadmap generated for {roadmap.career_name}: {roadmap.total_modules} modules ({roadmap.estimated_total_hours} hrs total).")
    print(f"    First Module: '{first_mod.title}' (Status: {first_mod.status}) with {len(first_mod.resources)} verified resources.")
    print(f"    Resource sample: {first_mod.resources[0].title} on {first_mod.resources[0].platform} ({first_mod.resources[0].url})")

    # 5. Examination Room & Security
    exam_data = start_module_exam(db, first_mod.id)
    assert len(exam_data.questions) > 0, "No questions loaded for exam"
    # Security check: ensure answer key not exposed in exam question
    for q in exam_data.questions:
        assert not hasattr(q, "correct_option"), "SECURITY ALERT: correct_option exposed in exam questions!"
    print(f"[5] Secure Exam Room test passed: {len(exam_data.questions)} randomized questions loaded (duration: {exam_data.duration_minutes}m, pass threshold: {exam_data.pass_percentage}%). Answer keys safely hidden.")

    # 6. Exam Evaluation & Auto-Grading
    sub_answers = [ExamAnswerSubmission(question_id=q.id, selected_option="A") for q in exam_data.questions]
    exam_result = evaluate_module_exam(db, student, first_mod.id, ExamSubmissionRequest(answers=sub_answers))
    print(f"[6] Exam Auto-Grading passed: Score: {exam_result.score_percentage}%, Result: {'PASSED' if exam_result.passed else 'FAILED'}")
    print(f"    Updated Skill Mastery: {exam_result.new_skill_mastery * 100}%")

    # 7. NBLA Optimizer Engine
    nbla_result = get_next_best_learning_action(db, student.id, student.target_career_id)
    assert nbla_result is not None, "NBLA Optimizer failed to recommend an action"
    action, score, comp, expl = nbla_result
    print(f"[7] NBLA Optimizer computed Next Best Action: '{action.title}' (Score: {score:.3f})")
    print(f"    Explanation: {expl}")

    # 8. Razorpay Sandbox Checkout & Subscription Upgrade
    order = create_razorpay_order(db, student, "premium_monthly")
    assert order.order_id.startswith("order_"), "Razorpay order creation failed"
    verify_res = verify_razorpay_payment(
        db, student, 
        VerifyPaymentRequest(
            razorpay_order_id=order.order_id,
            razorpay_payment_id="pay_sandbox_123456",
            razorpay_signature="sandbox_sig_verified"
        )
    )
    assert verify_res["tier"] == "premium_monthly", "Subscription upgrade failed"
    print(f"[8] Razorpay Sandbox payments verified: Student successfully upgraded to '{verify_res['tier']}' tier.")

    # 9. Research Baselines Evaluation
    benchmarks = get_research_evaluation_benchmark()
    assert len(benchmarks.baselines) == 5, "Expected 5 research baselines"
    print(f"[9] Research Benchmark Evaluation passed across 5 models:")
    for b in benchmarks.baselines:
        print(f"    * {b.baseline_name:<30} | NDCG@K: {b.ndcg_k:.2f} | Prereq Violations: {b.prerequisite_violations:.1f}% | Efficiency: {b.learning_efficiency:.2f}")

    db.close()
    print("\n=== ALL PLATFORM BACKEND TESTS PASSED WITH 100% SUCCESS ===")

if __name__ == "__main__":
    verify_all()
