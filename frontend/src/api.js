const API_BASE = 
  import.meta.env.VITE_API_BASE_URL || 
  (typeof window !== "undefined" && window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1"
    ? "https://skillpath-backend-1d08.onrender.com/api"
    : "http://localhost:8000/api");

function getHeaders() {
  const token = localStorage.getItem("edupath_token");
  const headers = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

// ================= AUTHENTICATION =================
export async function registerUser(name, email, password, role = "student") {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password, role })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Registration failed" }));
    throw new Error(err.detail || "Registration failed");
  }
  const data = await res.json();
  if (data.access_token) {
    localStorage.setItem("edupath_token", data.access_token);
  }
  return data;
}

export async function loginUser(email, password) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Invalid email or password" }));
    throw new Error(err.detail || "Invalid email or password");
  }
  const data = await res.json();
  if (data.access_token) {
    localStorage.setItem("edupath_token", data.access_token);
  }
  return data;
}

export async function fetchCurrentUser() {
  const res = await fetch(`${API_BASE}/auth/me`, { headers: getHeaders() });
  if (!res.ok) throw new Error("Unauthorized");
  return res.json();
}

export async function updateLearnerProfile(profileData) {
  const res = await fetch(`${API_BASE}/auth/profile`, {
    method: "PUT",
    headers: getHeaders(),
    body: JSON.stringify(profileData)
  });
  if (!res.ok) throw new Error("Failed to update profile");
  return res.json();
}

export function logoutUser() {
  localStorage.removeItem("edupath_token");
}

// ================= CAREER SELECTION & AI MATCHER =================
export async function fetchCareers() {
  const res = await fetch(`${API_BASE}/careers`);
  if (!res.ok) throw new Error("Failed to fetch careers");
  return res.json();
}

export async function fetchCareerRecommendations() {
  const res = await fetch(`${API_BASE}/careers/recommendations`, { headers: getHeaders() });
  if (!res.ok) throw new Error("Failed to fetch career recommendations");
  return res.json();
}

export async function selectTargetCareer(careerId) {
  const res = await fetch(`${API_BASE}/careers/select/${careerId}`, {
    method: "POST",
    headers: getHeaders()
  });
  if (!res.ok) throw new Error("Failed to select career");
  return res.json();
}

// ================= ADAPTIVE ROADMAP & RESOURCES =================
export async function fetchRoadmap() {
  const res = await fetch(`${API_BASE}/roadmap`, { headers: getHeaders() });
  if (!res.ok) throw new Error("Failed to load roadmap");
  return res.json();
}

export async function updateResourceProgress(resourceId, status, minutesSpent = 0) {
  const res = await fetch(`${API_BASE}/resources/${resourceId}/status`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ status, minutes_spent: minutesSpent })
  });
  if (!res.ok) throw new Error("Failed to update resource progress");
  return res.json();
}

// ================= MODULE EXAMINATIONS =================
export async function fetchModuleExam(moduleId) {
  const res = await fetch(`${API_BASE}/modules/${moduleId}/exam`, { headers: getHeaders() });
  if (!res.ok) throw new Error("Failed to start module exam");
  return res.json();
}

export async function submitModuleExam(moduleId, answers) {
  const res = await fetch(`${API_BASE}/modules/${moduleId}/exam/submit`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ answers })
  });
  if (!res.ok) throw new Error("Failed to submit exam");
  return res.json();
}

// ================= DASHBOARD & NBLA OPTIMIZER =================
export async function fetchDashboard(userId = null) {
  const endpoint = userId ? `${API_BASE}/users/${userId}/dashboard` : `${API_BASE}/dashboard`;
  const res = await fetch(endpoint, { headers: getHeaders() });
  if (!res.ok) throw new Error("Failed to fetch dashboard data");
  return res.json();
}

export async function completeAction(userId, actionId, performanceScore = null) {
  const res = await fetch(`${API_BASE}/users/${userId}/actions/${actionId}/complete`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ performance_score: performanceScore })
  });
  if (!res.ok) throw new Error("Failed to complete action");
  return res.json();
}

// ================= PAYMENTS & RAZORPAY SANDBOX =================
export async function fetchPlans() {
  const res = await fetch(`${API_BASE}/payments/plans`);
  if (!res.ok) throw new Error("Failed to fetch plans");
  return res.json();
}

export async function createPaymentOrder(planCode) {
  const res = await fetch(`${API_BASE}/payments/order`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({ plan_code: planCode })
  });
  if (!res.ok) throw new Error("Failed to create payment order");
  return res.json();
}

export async function verifyPayment(orderId, paymentId, signature) {
  const res = await fetch(`${API_BASE}/payments/verify`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({
      razorpay_order_id: orderId,
      razorpay_payment_id: paymentId,
      razorpay_signature: signature
    })
  });
  if (!res.ok) throw new Error("Payment verification failed");
  return res.json();
}

// ================= RESEARCH EVALUATION BENCHMARKS =================
export async function fetchResearchBenchmarks() {
  const res = await fetch(`${API_BASE}/research/evaluation`);
  if (!res.ok) throw new Error("Failed to fetch research benchmarks");
  return res.json();
}

// ================= ADMIN TELEMETRY =================
export async function fetchAdminOverview() {
  const res = await fetch(`${API_BASE}/admin/overview`, { headers: getHeaders() });
  if (!res.ok) throw new Error("Failed to fetch admin overview");
  return res.json();
}

export async function fetchAdminUsers() {
  const res = await fetch(`${API_BASE}/admin/users`, { headers: getHeaders() });
  if (!res.ok) throw new Error("Failed to fetch user directory");
  return res.json();
}

export async function fetchAdminEmails() {
  const res = await fetch(`${API_BASE}/admin/emails`, { headers: getHeaders() });
  if (!res.ok) throw new Error("Failed to fetch email logs");
  return res.json();
}

export async function fetchAdminPayments() {
  const res = await fetch(`${API_BASE}/admin/payments`, { headers: getHeaders() });
  if (!res.ok) throw new Error("Failed to fetch payments");
  return res.json();
}
