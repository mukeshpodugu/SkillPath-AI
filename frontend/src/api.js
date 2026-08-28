const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

export async function fetchCareers() {
  const res = await fetch(`${API_BASE}/careers`);
  if (!res.ok) throw new Error("Failed to fetch careers");
  return res.json();
}

export async function onboardUser(name, targetCareerId, knownSkillIds) {
  const res = await fetch(`${API_BASE}/users/onboard`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, target_career_id: targetCareerId, known_skill_ids: knownSkillIds })
  });
  if (!res.ok) throw new Error("Onboarding failed");
  return res.json();
}

export async function submitDiagnostic(userId, answers) {
  const res = await fetch(`${API_BASE}/users/${userId}/diagnostic`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers })
  });
  if (!res.ok) throw new Error("Failed to submit diagnostic test");
  return res.json();
}

export async function fetchDashboard(userId) {
  const res = await fetch(`${API_BASE}/users/${userId}/dashboard`);
  if (!res.ok) throw new Error("Failed to fetch dashboard data");
  return res.json();
}

export async function completeAction(userId, actionId, performanceScore = null) {
  const res = await fetch(`${API_BASE}/users/${userId}/actions/${actionId}/complete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ performance_score: performanceScore })
  });
  if (!res.ok) throw new Error("Failed to complete action");
  return res.json();
}
