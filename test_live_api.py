import urllib.request
import json
import time

BASE_URL = "https://skillpath-backend-7ozf.onrender.com/api"

def make_request(path, method="GET", body=None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"HTTPError {e.code}: {err_body}")
        raise

def run_e2e_check():
    print("=== LIVE END-TO-END VERIFICATION OF SKILLPATH AI ===")
    
    # 1. Check Careers
    careers = make_request("/careers")
    print(f"\n[Step 1] Careers loaded: {[c['name'] for c in careers]}")
    mle = next(c for c in careers if c["name"] == "Machine Learning Engineer")
    
    # 2. Onboarding User
    print("\n[Step 2] Testing Learner Onboarding (Target: Machine Learning Engineer, Claimed skills: Python [1])...")
    onboard_payload = {
        "name": "Audit Verification Learner",
        "target_career_id": mle["id"],
        "known_skill_ids": [1] # Python
    }
    onboard_res = make_request("/users/onboard", method="POST", body=onboard_payload)
    user_id = onboard_res["user"]["id"]
    questions = onboard_res["questions"]
    print(f"-> Created User ID: {user_id}")
    print(f"-> Diagnostic Questions served: {len(questions)} questions")
    for q in questions:
        print(f"   * Q: {q['text'][:60]}...")

    # 3. Submitting Diagnostic Exam
    print("\n[Step 3] Submitting Diagnostic Exam Answers...")
    diag_payload = {
        "answers": [
            {"question_id": q["id"], "selected_option": "A"} for q in questions
        ]
    }
    diag_res = make_request(f"/users/{user_id}/diagnostic", method="POST", body=diag_payload)
    print(f"-> Diagnostic Exam Result: {diag_res}")

    # 4. Checking Dashboard & NBLA Optimizer
    print("\n[Step 4] Checking Dashboard & NBLA Optimizer calculation...")
    dashboard = make_request(f"/users/{user_id}/dashboard")
    print(f"-> Career: {dashboard['career_name']}")
    print(f"-> Career Readiness: {dashboard['career_readiness'] * 100}%")
    print("-> Skills Mastery Profile:")
    for s in dashboard["skills_states"]:
        print(f"   * {s['skill_name']:<18} | Current: {int(s['mastery']*100)}% | Required: {int(s['required_mastery']*100)}% | Importance: {s['importance']}")

    nbla = dashboard.get("next_best_action")
    assert nbla is not None, "Error: NBLA was not generated!"
    action = nbla["action"]
    explanation = nbla["explanation"]
    
    print("\n[Step 5] NBLA Recommendation Output:")
    print(f"-> Recommended Action: \"{action['title']}\" ({action['action_type']})")
    print(f"-> Action Score: {nbla['action_score']}")
    print(f"-> Targeted Skill: {action['skill_name']}")
    print(f"-> Estimated Effort: {action['learning_effort']} mins")
    print(f"-> Expected Gain: +{int(action['expected_gain']*100)}%")
    print(f"-> Score Components: {explanation['components']}")
    print(f"-> Generated Explanation:\n   \"{explanation['summary']}\"")

    # Verify prerequisite blocking
    # Deep Learning and MLOps should NOT be recommended because their prerequisites (ML, Linear Algebra) are not met
    assert action["skill_name"] not in ["Deep Learning", "MLOps"], "Prerequisite constraint failed!"
    print("\n-> Prerequisite constraint check PASSED: Advanced topics are properly locked.")

    # 6. Simulate Completing Recommended Action
    print("\n[Step 6] Testing Continuous Re-optimization Feedback Loop...")
    complete_res = make_request(f"/users/{user_id}/actions/{action['id']}/complete", method="POST", body={})
    print(f"-> Action completed. Updated Career Readiness: {complete_res['career_readiness'] * 100}%")
    new_nbla = complete_res.get("next_best_action")
    if new_nbla:
        print(f"-> New NBLA dynamically recommended: \"{new_nbla['action']['title']}\" for skill \"{new_nbla['action']['skill_name']}\"")
        print(f"-> New Action Score: {new_nbla['action_score']}")

    print("\n=== ALL CHECKS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_e2e_check()
