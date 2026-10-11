import React, { useState, useEffect } from 'react';
import { 
  registerUser, loginUser, fetchCurrentUser, updateLearnerProfile, logoutUser,
  fetchCareers, fetchCareerRecommendations, selectTargetCareer,
  fetchRoadmap, updateResourceProgress, fetchModuleExam, submitModuleExam,
  fetchDashboard, completeAction, fetchPlans, createPaymentOrder, verifyPayment,
  fetchResearchBenchmarks, fetchAdminOverview, fetchAdminUsers, fetchAdminEmails, fetchAdminPayments
} from './api';
import { 
  Compass, BookOpen, CheckCircle2, Lock, PlayCircle, Star, 
  Target, Award, Clock, ArrowRight, ShieldCheck, Check, 
  ExternalLink, BarChart3, Users, CreditCard, Mail, Sparkles, 
  FileCheck, AlertCircle, LogOut, User, RefreshCw, Zap
} from 'lucide-react';

export default function App() {
  // Navigation: 'dashboard' | 'career-explorer' | 'roadmap' | 'research' | 'pricing' | 'admin'
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // User State
  const [currentUser, setCurrentUser] = useState(null);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState('login'); // 'login' | 'register'
  const [authForm, setAuthForm] = useState({ name: '', email: '', password: '', role: 'student' });

  // Data States
  const [dashboardData, setDashboardData] = useState(null);
  const [roadmapData, setRoadmapData] = useState(null);
  const [careerRecs, setCareerRecs] = useState([]);
  const [plans, setPlans] = useState([]);
  const [researchData, setResearchData] = useState(null);
  const [adminStats, setAdminStats] = useState(null);
  const [adminUsers, setAdminUsers] = useState([]);
  const [adminEmails, setAdminEmails] = useState([]);

  // Exam Modal State
  const [examModalOpen, setExamModalOpen] = useState(false);
  const [examData, setExamData] = useState(null);
  const [examAnswers, setExamAnswers] = useState({});
  const [examResult, setExamResult] = useState(null);
  const [currentModuleId, setCurrentModuleId] = useState(null);
  const [examTimer, setExamTimer] = useState(15 * 60);

  // Action completion in progress
  const [completingActionId, setCompletingActionId] = useState(null);

  // Initial bootstrap
  useEffect(() => {
    bootstrapApp();
  }, []);

  async function bootstrapApp() {
    setLoading(true);
    try {
      // Check if existing token
      const token = localStorage.getItem("edupath_token");
      if (token) {
        try {
          const user = await fetchCurrentUser();
          setCurrentUser(user);
          await loadUserData(user);
        } catch (err) {
          localStorage.removeItem("edupath_token");
          // Fallback: auto-login as demo student if no valid session
          await handleQuickLogin('student@edupath.ai', 'password123');
        }
      } else {
        // Auto-login as demo student to make reviewing instant
        await handleQuickLogin('student@edupath.ai', 'password123');
      }
    } catch (e) {
      console.warn("Bootstrap error:", e);
    } finally {
      setLoading(false);
    }
  }

  async function loadUserData(user) {
    try {
      const [dash, road, recs, plansList, bench] = await Promise.all([
        fetchDashboard().catch(() => null),
        fetchRoadmap().catch(() => null),
        fetchCareerRecommendations().catch(() => []),
        fetchPlans().catch(() => []),
        fetchResearchBenchmarks().catch(() => null)
      ]);
      setDashboardData(dash);
      setRoadmapData(road);
      setCareerRecs(recs);
      setPlans(plansList);
      setResearchData(bench);

      if (user.role === 'admin') {
        const [stats, uList, eList] = await Promise.all([
          fetchAdminOverview().catch(() => null),
          fetchAdminUsers().catch(() => []),
          fetchAdminEmails().catch(() => [])
        ]);
        setAdminStats(stats);
        setAdminUsers(uList);
        setAdminEmails(eList);
      }
    } catch (err) {
      console.error("Error loading user data:", err);
    }
  }

  async function handleAuthSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      let res;
      if (authMode === 'register') {
        res = await registerUser(authForm.name, authForm.email, authForm.password, authForm.role);
      } else {
        res = await loginUser(authForm.email, authForm.password);
      }
      setCurrentUser(res.user);
      setAuthModalOpen(false);
      setSuccessMsg(`Welcome, ${res.user.name}!`);
      await loadUserData(res.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleQuickLogin(email, password) {
    setLoading(true);
    setError(null);
    try {
      const res = await loginUser(email, password);
      setCurrentUser(res.user);
      await loadUserData(res.user);
      setSuccessMsg(`Signed in as ${res.user.name} (${res.user.role})`);
    } catch (err) {
      setError("Failed to sign in demo user. Please make sure backend is running.");
    } finally {
      setLoading(false);
    }
  }

  function handleLogout() {
    logoutUser();
    setCurrentUser(null);
    setDashboardData(null);
    setRoadmapData(null);
    setActiveTab('dashboard');
    setSuccessMsg("Logged out successfully.");
  }

  async function handleSelectCareer(careerId) {
    setLoading(true);
    try {
      const updatedUser = await selectTargetCareer(careerId);
      setCurrentUser(updatedUser);
      await loadUserData(updatedUser);
      setSuccessMsg(`Target career updated to ${updatedUser.career ? updatedUser.career.name : 'new role'}!`);
      setActiveTab('roadmap');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleCompleteAction(actionId) {
    if (!currentUser) return;
    setCompletingActionId(actionId);
    try {
      const updated = await completeAction(currentUser.id, actionId);
      setDashboardData(updated);
      const road = await fetchRoadmap().catch(() => null);
      setRoadmapData(road);
      setSuccessMsg("Activity completed! Mastery updated and NBLA recomputed.");
    } catch (err) {
      setError(err.message);
    } finally {
      setCompletingActionId(null);
    }
  }

  async function handleStartExam(moduleId) {
    setLoading(true);
    setError(null);
    setExamResult(null);
    setExamAnswers({});
    setCurrentModuleId(moduleId);
    try {
      const exam = await fetchModuleExam(moduleId);
      setExamData(exam);
      setExamTimer(exam.duration_minutes * 60);
      setExamModalOpen(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmitExam(e) {
    e.preventDefault();
    if (!examData || !currentModuleId) return;
    setLoading(true);
    try {
      const answersPayload = Object.entries(examAnswers).map(([qId, opt]) => ({
        question_id: parseInt(qId),
        selected_option: opt
      }));
      const result = await submitModuleExam(currentModuleId, answersPayload);
      setExamResult(result);
      // Refresh dashboard & roadmap
      if (currentUser) {
        await loadUserData(currentUser);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleUpgradePlan(planCode) {
    if (planCode === 'free') return;
    setLoading(true);
    try {
      const order = await createPaymentOrder(planCode);
      // Simulate Sandbox Checkout
      const simulatedPaymentId = `pay_sandbox_${Date.now()}`;
      const verifyRes = await verifyPayment(
        order.order_id,
        simulatedPaymentId,
        "sandbox_sig_verified"
      );
      setSuccessMsg(verifyRes.message);
      if (currentUser) {
        const u = await fetchCurrentUser();
        setCurrentUser(u);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleToggleResource(resourceId, currentStatus) {
    const nextStatus = currentStatus === 'completed' ? 'not_started' : 'completed';
    try {
      await updateResourceProgress(resourceId, nextStatus, nextStatus === 'completed' ? 45 : 0);
      const road = await fetchRoadmap();
      setRoadmapData(road);
      const dash = await fetchDashboard();
      setDashboardData(dash);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: '#0f172a', color: '#f8fafc', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      
      {/* Dynamic CSS Styling */}
      <style>{`
        * { box-sizing: border-box; }
        button { cursor: pointer; transition: all 0.15s ease; border: none; outline: none; }
        button:hover { filter: brightness(1.08); }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        .nav-btn {
          display: flex; align-items: center; gap: 0.5rem; padding: 0.6rem 0.9rem;
          border-radius: 0.5rem; font-size: 0.875rem; font-weight: 500; color: #94a3b8;
          background: transparent;
        }
        .nav-btn:hover, .nav-btn.active {
          color: #38bdf8; background: #1e293b;
        }
        .card {
          background-color: #1e293b; border: 1px solid #334155;
          border-radius: 0.75rem; padding: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2);
        }
        .badge {
          display: inline-flex; align-items: center; gap: 0.25rem; padding: 0.2rem 0.55rem;
          border-radius: 9999px; font-size: 0.75rem; font-weight: 600;
        }
        input, select {
          background: #0f172a; border: 1px solid #334155; color: #f8fafc;
          padding: 0.65rem 0.85rem; border-radius: 0.5rem; font-size: 0.9rem; outline: none;
        }
        input:focus, select:focus { border-color: #38bdf8; }
      `}</style>

      {/* TOP NAVIGATION BAR */}
      <nav style={{ backgroundColor: '#0f172a', borderBottom: '1px solid #1e293b', position: 'sticky', top: 0, zIndex: 40, padding: '0.75rem 1.5rem' }}>
        <div style={{ maxWidth: '1300px', margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          
          {/* Logo & Platform Name */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }} onClick={() => setActiveTab('dashboard')}>
            <div style={{ width: '38px', height: '38px', backgroundColor: '#0284c7', borderRadius: '0.5rem', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 'bold' }}>
              <Compass size={22} />
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: '1.2rem', color: '#f8fafc', letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                EduPath AI <span style={{ fontSize: '0.7rem', backgroundColor: '#0369a1', padding: '0.1rem 0.4rem', borderRadius: '0.25rem', color: '#e0f2fe' }}>PROD</span>
              </div>
              <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Adaptive Learning Path Optimizer</div>
            </div>
          </div>

          {/* Navigation Links */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', flexWrap: 'wrap' }}>
            <button className={`nav-btn ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('dashboard')}>
              <BarChart3 size={16} /> Dashboard
            </button>
            <button className={`nav-btn ${activeTab === 'career-explorer' ? 'active' : ''}`} onClick={() => setActiveTab('career-explorer')}>
              <Target size={16} /> Career Explorer
            </button>
            <button className={`nav-btn ${activeTab === 'roadmap' ? 'active' : ''}`} onClick={() => setActiveTab('roadmap')}>
              <BookOpen size={16} /> Roadmap & Exams
            </button>
            <button className={`nav-btn ${activeTab === 'research' ? 'active' : ''}`} onClick={() => setActiveTab('research')}>
              <Sparkles size={16} /> Research Lab
            </button>
            <button className={`nav-btn ${activeTab === 'pricing' ? 'active' : ''}`} onClick={() => setActiveTab('pricing')}>
              <CreditCard size={16} /> Plans
            </button>
            {currentUser?.role === 'admin' && (
              <button className={`nav-btn ${activeTab === 'admin' ? 'active' : ''}`} onClick={() => setActiveTab('admin')}>
                <ShieldCheck size={16} color="#38bdf8" /> Admin Portal
              </button>
            )}
          </div>

          {/* User Account Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            {currentUser ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{ textAlign: 'right', display: 'none', md: 'block' }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f8fafc' }}>{currentUser.name}</div>
                  <div style={{ display: 'flex', gap: '0.3rem', justifyContent: 'flex-end' }}>
                    <span className="badge" style={{ backgroundColor: '#1e3a8a', color: '#93c5fd' }}>{currentUser.role}</span>
                    <span className="badge" style={{ backgroundColor: currentUser.subscription_tier.includes('premium') ? '#701a75' : '#334155', color: '#f0abfc' }}>
                      {currentUser.subscription_tier.includes('premium') ? 'PRO' : 'FREE'}
                    </span>
                  </div>
                </div>
                <button 
                  onClick={handleLogout}
                  style={{ padding: '0.5rem', backgroundColor: '#334155', borderRadius: '0.5rem', color: '#cbd5e1' }}
                  title="Sign out"
                >
                  <LogOut size={16} />
                </button>
              </div>
            ) : (
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button 
                  onClick={() => { setAuthMode('login'); setAuthModalOpen(true); }}
                  style={{ padding: '0.5rem 0.9rem', backgroundColor: '#334155', color: '#f8fafc', borderRadius: '0.5rem', fontSize: '0.85rem', fontWeight: 600 }}
                >
                  Log In
                </button>
                <button 
                  onClick={() => { setAuthMode('register'); setAuthModalOpen(true); }}
                  style={{ padding: '0.5rem 0.9rem', backgroundColor: '#0284c7', color: 'white', borderRadius: '0.5rem', fontSize: '0.85rem', fontWeight: 600 }}
                >
                  Sign Up
                </button>
              </div>
            )}
          </div>

        </div>
      </nav>

      {/* NOTIFICATION BANNERS */}
      <div style={{ maxWidth: '1300px', margin: '0 auto', width: '100%', padding: '0.75rem 1.5rem 0' }}>
        {error && (
          <div style={{ padding: '0.75rem 1rem', backgroundColor: '#450a0a', border: '1px solid #991b1b', color: '#fca5a5', borderRadius: '0.5rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.875rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <AlertCircle size={18} /> <span>{error}</span>
            </div>
            <button onClick={() => setError(null)} style={{ background: 'transparent', color: '#fca5a5' }}>✕</button>
          </div>
        )}
        {successMsg && (
          <div style={{ padding: '0.75rem 1rem', backgroundColor: '#064e3b', border: '1px solid #065f46', color: '#6ee7b7', borderRadius: '0.5rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.875rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <CheckCircle2 size={18} /> <span>{successMsg}</span>
            </div>
            <button onClick={() => setSuccessMsg(null)} style={{ background: 'transparent', color: '#6ee7b7' }}>✕</button>
          </div>
        )}
      </div>

      {/* MAIN CONTAINER CONTENT */}
      <main style={{ maxWidth: '1300px', margin: '0 auto', width: '100%', padding: '1rem 1.5rem 3rem', flex: 1 }}>

        {/* ================= 1. DASHBOARD VIEW ================= */}
        {activeTab === 'dashboard' && dashboardData && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            
            {/* Top Stat Row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
              
              {/* Career Readiness Gauge Card */}
              <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
                <div style={{ position: 'relative', width: '80px', height: '80px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <svg width="80" height="80" viewBox="0 0 36 36" style={{ transform: 'rotate(-90deg)' }}>
                    <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#334155" strokeWidth="3.5" />
                    <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#38bdf8" strokeDasharray={`${dashboardData.career_readiness * 100}, 100`} strokeWidth="3.5" strokeLinecap="round" />
                  </svg>
                  <div style={{ position: 'absolute', fontSize: '1.1rem', fontWeight: 700, color: '#38bdf8' }}>
                    {Math.round(dashboardData.career_readiness * 100)}%
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Career Readiness</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>{dashboardData.career_name}</div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Estimated by O*NET weights</div>
                </div>
              </div>

              {/* Study Streak */}
              <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
                <div style={{ width: '56px', height: '56px', borderRadius: '0.75rem', backgroundColor: '#78350f', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f59e0b' }}>
                  <Zap size={28} />
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase' }}>Study Streak</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#f59e0b' }}>{dashboardData.study_streak_days} Days Active</div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Daily adaptive progress</div>
                </div>
              </div>

              {/* Time Logged */}
              <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
                <div style={{ width: '56px', height: '56px', borderRadius: '0.75rem', backgroundColor: '#064e3b', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#10b981' }}>
                  <Clock size={28} />
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase' }}>Time Invested</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#10b981' }}>
                    {Math.round(dashboardData.total_study_minutes / 60 * 10) / 10} Hours
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Across resources & exams</div>
                </div>
              </div>

              {/* Modules Completed */}
              <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
                <div style={{ width: '56px', height: '56px', borderRadius: '0.75rem', backgroundColor: '#431407', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f97316' }}>
                  <Award size={28} />
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase' }}>Modules Passed</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#f97316' }}>
                    {dashboardData.completed_modules_count} / {dashboardData.total_modules_count}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Passed module exams</div>
                </div>
              </div>

            </div>

            {/* Split Grid: NBLA Recommendation on Left, Skills Matrix on Right */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem', alignItems: 'start' }}>
              
              {/* NBLA CARD (Heart of the Research) */}
              <div className="card" style={{ border: '2px solid #0284c7', position: 'relative' }}>
                <div style={{ position: 'absolute', top: '-11px', left: '1.25rem', backgroundColor: '#0284c7', color: 'white', padding: '0.15rem 0.65rem', borderRadius: '9999px', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.05em' }}>
                  NEXT BEST LEARNING ACTION (NBLA)
                </div>

                {dashboardData.next_best_action ? (
                  <div style={{ marginTop: '0.5rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                      <span className="badge" style={{ backgroundColor: '#0369a1', color: '#e0f2fe' }}>
                        {dashboardData.next_best_action.action.action_type}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                        Optimization Score: <strong>{dashboardData.next_best_action.action_score}</strong>
                      </span>
                    </div>

                    <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc' }}>
                      {dashboardData.next_best_action.action.title}
                    </h3>
                    <p style={{ margin: '0 0 1rem 0', color: '#cbd5e1', fontSize: '0.875rem', lineHeight: 1.5 }}>
                      {dashboardData.next_best_action.action.description}
                    </p>

                    <div style={{ display: 'flex', gap: '1rem', padding: '0.75rem', backgroundColor: '#0f172a', borderRadius: '0.5rem', marginBottom: '1rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.8rem', color: '#94a3b8' }}>
                        <Clock size={15} color="#38bdf8" /> Effort: <strong>{dashboardData.next_best_action.action.learning_effort} mins</strong>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.8rem', color: '#94a3b8' }}>
                        <Award size={15} color="#4ade80" /> Expected Gain: <strong>+{Math.round(dashboardData.next_best_action.action.expected_gain * 100)}%</strong>
                      </div>
                    </div>

                    {/* Explainability Engine */}
                    <div style={{ padding: '0.9rem', backgroundColor: '#0c4a6e', border: '1px solid #075985', borderRadius: '0.5rem', marginBottom: '1.25rem' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#7dd3fc', marginBottom: '0.35rem', textTransform: 'uppercase' }}>
                        Optimizer Explainability Vector
                      </div>
                      <p style={{ margin: 0, fontSize: '0.825rem', color: '#e0f2fe', lineHeight: 1.4, fontStyle: 'italic' }}>
                        {dashboardData.next_best_action.explanation.summary}
                      </p>
                      
                      <div style={{ marginTop: '0.65rem', paddingTop: '0.65rem', borderTop: '1px solid #0369a1', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.35rem', fontSize: '0.75rem', color: '#bae6fd' }}>
                        <div>Skill Gap: <strong>+{dashboardData.next_best_action.explanation.components.gap_contribution}</strong></div>
                        <div>Role Importance: <strong>+{dashboardData.next_best_action.explanation.components.importance_contribution}</strong></div>
                        <div>Prerequisite Enablement: <strong>+{dashboardData.next_best_action.explanation.components.prerequisite_contribution}</strong></div>
                        <div>Expected Gain: <strong>+{dashboardData.next_best_action.explanation.components.gain_contribution}</strong></div>
                        <div style={{ color: '#fca5a5' }}>Effort Penalty: <strong>{dashboardData.next_best_action.explanation.components.effort_penalty}</strong></div>
                      </div>
                    </div>

                    <button 
                      onClick={() => handleCompleteAction(dashboardData.next_best_action.action.id)}
                      disabled={completingActionId !== null}
                      style={{ width: '100%', padding: '0.75rem', backgroundColor: '#0284c7', color: 'white', borderRadius: '0.5rem', fontWeight: 600, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem' }}
                    >
                      {completingActionId ? "Re-optimizing..." : "Complete Action & Re-optimize Path"}
                      <PlayCircle size={18} />
                    </button>
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: '2rem 0', color: '#4ade80' }}>
                    <CheckCircle2 size={40} style={{ margin: '0 auto 0.5rem' }} />
                    <div style={{ fontWeight: 700 }}>Roadmap Completed!</div>
                    <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>You have reached target mastery for this career role.</div>
                  </div>
                )}
              </div>

              {/* SKILLS MASTERY BREAKDOWN */}
              <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600 }}>Skills Competency Matrix</h3>
                  <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Target vs Current</span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {dashboardData.skills_states.map(s => {
                    const isMastered = s.mastery >= s.required_mastery;
                    return (
                      <div key={s.skill_id} style={{ borderBottom: '1px solid #334155', paddingBottom: '0.75rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem', fontSize: '0.85rem' }}>
                          <span style={{ fontWeight: 600, color: '#f8fafc' }}>{s.skill_name}</span>
                          <span style={{ color: isMastered ? '#4ade80' : '#38bdf8' }}>
                            {Math.round(s.mastery * 100)}% / {Math.round(s.required_mastery * 100)}%
                          </span>
                        </div>
                        <div style={{ position: 'relative', width: '100%', height: '7px', backgroundColor: '#0f172a', borderRadius: '9999px', overflow: 'hidden' }}>
                          <div style={{ width: `${s.mastery * 100}%`, height: '100%', backgroundColor: isMastered ? '#22c55e' : '#0284c7', borderRadius: '9999px' }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

            </div>

          </div>
        )}

        {/* ================= 2. CAREER EXPLORER VIEW ================= */}
        {activeTab === 'career-explorer' && (
          <div>
            <div style={{ marginBottom: '1.5rem' }}>
              <h2 style={{ margin: '0 0 0.5rem 0', fontSize: '1.5rem', fontWeight: 700 }}>AI Career Recommender</h2>
              <p style={{ margin: 0, color: '#94a3b8', fontSize: '0.9rem' }}>
                Matches your existing skills and background against O*NET and ESCO occupational standards to recommend optimal career trajectories.
              </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '1.25rem' }}>
              {careerRecs.map(cr => (
                <div key={cr.career.id} className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                      <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700, color: '#f8fafc' }}>
                        {cr.career.name}
                      </h3>
                      <span className="badge" style={{ backgroundColor: '#0c4a6e', color: '#38bdf8', fontSize: '0.85rem' }}>
                        {cr.compatibility_score}% Match
                      </span>
                    </div>

                    <p style={{ margin: '0 0 0.75rem 0', color: '#94a3b8', fontSize: '0.85rem', lineHeight: 1.4 }}>
                      {cr.career.description}
                    </p>

                    <div style={{ padding: '0.75rem', backgroundColor: '#0f172a', borderRadius: '0.5rem', marginBottom: '1rem', fontSize: '0.8rem' }}>
                      <div style={{ color: '#38bdf8', fontWeight: 600, marginBottom: '0.25rem' }}>Recommendation Rationale:</div>
                      <div style={{ color: '#cbd5e1' }}>{cr.match_rationale}</div>
                    </div>

                    {/* Matched & Missing skills */}
                    <div style={{ marginBottom: '1rem' }}>
                      <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.35rem' }}>Matched Skills:</div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', marginBottom: '0.75rem' }}>
                        {cr.matched_skills.map(s => (
                          <span key={s} className="badge" style={{ backgroundColor: '#064e3b', color: '#6ee7b7' }}>✓ {s}</span>
                        ))}
                      </div>

                      <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.35rem' }}>Skills to Develop:</div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                        {cr.missing_or_weak_skills.map(s => (
                          <span key={s} className="badge" style={{ backgroundColor: '#451a03', color: '#fdba74' }}>+ {s}</span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <button 
                    onClick={() => handleSelectCareer(cr.career.id)}
                    style={{ width: '100%', padding: '0.65rem', backgroundColor: '#0284c7', color: 'white', borderRadius: '0.5rem', fontWeight: 600, fontSize: '0.9rem', marginTop: '1rem' }}
                  >
                    Select Career & Generate Roadmap
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ================= 3. ADAPTIVE ROADMAP VIEW ================= */}
        {activeTab === 'roadmap' && roadmapData && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
              <div>
                <h2 style={{ margin: '0 0 0.25rem 0', fontSize: '1.5rem', fontWeight: 700 }}>
                  Personalized Roadmap: {roadmapData.career_name}
                </h2>
                <p style={{ margin: 0, color: '#94a3b8', fontSize: '0.875rem' }}>
                  {roadmapData.total_modules} Ordered Modules &bull; {roadmapData.completed_modules} Completed &bull; Est. {roadmapData.estimated_total_hours} Hours
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {roadmapData.modules.map((mod, idx) => {
                const isLocked = mod.status === 'locked';
                const isCompleted = mod.status === 'completed';

                return (
                  <div key={mod.id} className="card" style={{ opacity: isLocked ? 0.7 : 1, borderLeft: isCompleted ? '4px solid #22c55e' : (isLocked ? '4px solid #64748b' : '4px solid #0284c7') }}>
                    
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '0.75rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div style={{ width: '32px', height: '32px', borderRadius: '50%', backgroundColor: isCompleted ? '#15803d' : (isLocked ? '#334155' : '#0284c7'), display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '0.85rem' }}>
                          {isCompleted ? <Check size={16} /> : (isLocked ? <Lock size={14} /> : mod.order_index)}
                        </div>
                        <div>
                          <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc' }}>
                            {mod.title}
                          </h3>
                          <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                            Skill Target: <strong>{mod.skill_name}</strong> &bull; Current Mastery: {Math.round(mod.current_mastery * 100)}%
                          </div>
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span className="badge" style={{ backgroundColor: isCompleted ? '#064e3b' : (isLocked ? '#334155' : '#0c4a6e'), color: isCompleted ? '#4ade80' : (isLocked ? '#94a3b8' : '#38bdf8') }}>
                          {mod.status.toUpperCase()}
                        </span>
                        {!isLocked && (
                          <button 
                            onClick={() => handleStartExam(mod.id)}
                            style={{ padding: '0.45rem 0.85rem', backgroundColor: mod.has_passed_exam ? '#1e293b' : '#0284c7', border: '1px solid #0284c7', color: 'white', borderRadius: '0.4rem', fontSize: '0.8rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.35rem' }}
                          >
                            <FileCheck size={14} /> {mod.has_passed_exam ? "Retake Exam" : "Take Module Exam"}
                          </button>
                        )}
                      </div>
                    </div>

                    <p style={{ margin: '0 0 1rem 0', color: '#cbd5e1', fontSize: '0.85rem' }}>
                      {mod.description}
                    </p>

                    {/* Verified Learning Resources List */}
                    <div style={{ backgroundColor: '#0f172a', padding: '0.85rem', borderRadius: '0.5rem' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
                        Verified Learning Resources ({mod.resources.length})
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        {mod.resources.map(res => (
                          <div key={res.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.5rem', backgroundColor: '#1e293b', borderRadius: '0.4rem', fontSize: '0.825rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                              <span className="badge" style={{ backgroundColor: '#334155', color: '#cbd5e1' }}>{res.platform}</span>
                              <a href={res.url} target="_blank" rel="noopener noreferrer" style={{ color: '#38bdf8', textDecoration: 'none', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                                {res.title} <ExternalLink size={12} />
                              </a>
                            </div>

                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                              <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{res.estimated_duration_minutes}m</span>
                              <button 
                                onClick={() => handleToggleResource(res.id, res.user_status)}
                                style={{ padding: '0.25rem 0.5rem', borderRadius: '0.25rem', fontSize: '0.75rem', backgroundColor: res.user_status === 'completed' ? '#064e3b' : '#334155', color: res.user_status === 'completed' ? '#4ade80' : '#94a3b8' }}
                              >
                                {res.user_status === 'completed' ? "Completed ✓" : "Mark Done"}
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ================= 4. RESEARCH BENCHMARK VIEW ================= */}
        {activeTab === 'research' && researchData && (
          <div>
            <div style={{ marginBottom: '1.5rem' }}>
              <h2 style={{ margin: '0 0 0.5rem 0', fontSize: '1.5rem', fontWeight: 700 }}>
                Research Evaluation & Baselines Comparison
              </h2>
              <p style={{ margin: 0, color: '#94a3b8', fontSize: '0.9rem' }}>
                Empirical benchmark results comparing the proposed Career-Aware NBLA Optimizer against 4 standard research baselines (Table IV & V from Research Paper).
              </p>
            </div>

            <div className="card" style={{ overflowX: 'auto', marginBottom: '1.5rem' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #334155', color: '#94a3b8' }}>
                    <th style={{ padding: '0.75rem' }}>Baseline Algorithm</th>
                    <th style={{ padding: '0.75rem' }}>Precision@K</th>
                    <th style={{ padding: '0.75rem' }}>NDCG@K</th>
                    <th style={{ padding: '0.75rem' }}>Skill-Gap Reduction</th>
                    <th style={{ padding: '0.75rem' }}>Prereq Violations</th>
                    <th style={{ padding: '0.75rem' }}>Learning Efficiency</th>
                  </tr>
                </thead>
                <tbody>
                  {researchData.baselines.map((b, i) => {
                    const isProposed = b.baseline_name.includes("Proposed");
                    return (
                      <tr key={i} style={{ borderBottom: '1px solid #1e293b', backgroundColor: isProposed ? '#0c4a6e' : 'transparent', fontWeight: isProposed ? 600 : 400 }}>
                        <td style={{ padding: '0.75rem', color: isProposed ? '#38bdf8' : '#f8fafc' }}>{b.baseline_name}</td>
                        <td style={{ padding: '0.75rem' }}>{b.precision_k}</td>
                        <td style={{ padding: '0.75rem' }}>{b.ndcg_k}</td>
                        <td style={{ padding: '0.75rem' }}>{b.skill_gap_reduction}%</td>
                        <td style={{ padding: '0.75rem', color: b.prerequisite_violations < 10 ? '#4ade80' : '#f87171' }}>{b.prerequisite_violations}%</td>
                        <td style={{ padding: '0.75rem' }}>{b.learning_efficiency}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="card" style={{ backgroundColor: '#0f172a' }}>
              <h4 style={{ margin: '0 0 0.5rem 0', color: '#38bdf8', fontSize: '0.95rem' }}>Scientific Conclusion:</h4>
              <p style={{ margin: 0, color: '#cbd5e1', fontSize: '0.875rem', lineHeight: 1.5 }}>
                {researchData.analysis_conclusion}
              </p>
            </div>
          </div>
        )}

        {/* ================= 5. PRICING & SUBSCRIPTION VIEW ================= */}
        {activeTab === 'pricing' && (
          <div>
            <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
              <h2 style={{ margin: '0 0 0.5rem 0', fontSize: '1.75rem', fontWeight: 700 }}>Choose Your Learning Plan</h2>
              <p style={{ margin: 0, color: '#94a3b8', fontSize: '0.95rem' }}>
                Upgrade to Pro for multi-career roadmaps, advanced exams, and priority AI optimization.
              </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem', maxWidth: '1000px', margin: '0 auto' }}>
              {plans.map(p => {
                const isCurrent = currentUser?.subscription_tier === p.code;
                const isPro = p.code !== 'free';

                return (
                  <div key={p.code} className="card" style={{ border: isPro ? '2px solid #0284c7' : '1px solid #334155', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                    <div>
                      <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.25rem', fontWeight: 700 }}>{p.name}</h3>
                      <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f8fafc', marginBottom: '1rem' }}>
                        ₹{p.price_inr} <span style={{ fontSize: '0.85rem', fontWeight: 400, color: '#94a3b8' }}>/{p.billing_interval}</span>
                      </div>

                      <ul style={{ margin: 0, paddingLeft: '1.25rem', color: '#cbd5e1', fontSize: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        {p.features.map((feat, fi) => (
                          <li key={fi}>{feat}</li>
                        ))}
                      </ul>
                    </div>

                    <button 
                      onClick={() => handleUpgradePlan(p.code)}
                      disabled={isCurrent}
                      style={{ marginTop: '1.5rem', width: '100%', padding: '0.75rem', borderRadius: '0.5rem', fontWeight: 600, backgroundColor: isCurrent ? '#334155' : (isPro ? '#0284c7' : '#1e293b'), color: 'white' }}
                    >
                      {isCurrent ? "Current Active Plan" : (isPro ? "Upgrade Plan (Razorpay Sandbox)" : "Select Free")}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ================= 6. ADMIN PORTAL VIEW ================= */}
        {activeTab === 'admin' && currentUser?.role === 'admin' && (
          <div>
            <div style={{ marginBottom: '1.5rem' }}>
              <h2 style={{ margin: '0 0 0.25rem 0', fontSize: '1.5rem', fontWeight: 700 }}>Administrator Control Center</h2>
              <p style={{ margin: 0, color: '#94a3b8', fontSize: '0.875rem' }}>Platform health, registered users, and audit dispatches.</p>
            </div>

            {adminStats && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
                <div className="card">
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>TOTAL USERS</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{adminStats.total_users}</div>
                </div>
                <div className="card">
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>STUDENTS</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#38bdf8' }}>{adminStats.total_students}</div>
                </div>
                <div className="card">
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>EXAM ATTEMPTS</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#4ade80' }}>{adminStats.total_exam_attempts}</div>
                </div>
                <div className="card">
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>REVENUE</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#f59e0b' }}>₹{adminStats.total_revenue_inr}</div>
                </div>
              </div>
            )}

            {/* Users Directory Table */}
            <div className="card" style={{ overflowX: 'auto', marginBottom: '1.5rem' }}>
              <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem' }}>Registered Users Directory</h3>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #334155', color: '#94a3b8' }}>
                    <th style={{ padding: '0.5rem' }}>Name</th>
                    <th style={{ padding: '0.5rem' }}>Email</th>
                    <th style={{ padding: '0.5rem' }}>Role</th>
                    <th style={{ padding: '0.5rem' }}>Plan</th>
                    <th style={{ padding: '0.5rem' }}>Career Goal</th>
                  </tr>
                </thead>
                <tbody>
                  {adminUsers.map(u => (
                    <tr key={u.id} style={{ borderBottom: '1px solid #1e293b' }}>
                      <td style={{ padding: '0.5rem' }}>{u.name}</td>
                      <td style={{ padding: '0.5rem' }}>{u.email}</td>
                      <td style={{ padding: '0.5rem' }}><span className="badge" style={{ backgroundColor: '#1e3a8a' }}>{u.role}</span></td>
                      <td style={{ padding: '0.5rem' }}>{u.subscription_tier}</td>
                      <td style={{ padding: '0.5rem' }}>{u.career}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Transactional Emails Log Table */}
            <div className="card" style={{ overflowX: 'auto' }}>
              <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem' }}>Transactional Notification Audit Logs</h3>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #334155', color: '#94a3b8' }}>
                    <th style={{ padding: '0.5rem' }}>Recipient</th>
                    <th style={{ padding: '0.5rem' }}>Subject</th>
                    <th style={{ padding: '0.5rem' }}>Template</th>
                    <th style={{ padding: '0.5rem' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {adminEmails.map(l => (
                    <tr key={l.id} style={{ borderBottom: '1px solid #1e293b' }}>
                      <td style={{ padding: '0.5rem' }}>{l.recipient}</td>
                      <td style={{ padding: '0.5rem' }}>{l.subject}</td>
                      <td style={{ padding: '0.5rem' }}>{l.template}</td>
                      <td style={{ padding: '0.5rem' }}><span className="badge" style={{ backgroundColor: '#064e3b', color: '#6ee7b7' }}>{l.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

      </main>

      {/* ================= MODAL: MODULE EXAMINATION ROOM ================= */}
      {examModalOpen && examData && (
        <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.85)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50, padding: '1rem' }}>
          <div style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '0.75rem', width: '100%', maxWidth: '750px', maxHeight: '90vh', overflowY: 'auto', padding: '1.5rem' }}>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #334155', paddingBottom: '1rem', marginBottom: '1.25rem' }}>
              <div>
                <span className="badge" style={{ backgroundColor: '#0369a1', color: '#e0f2fe' }}>EXAM ROOM</span>
                <h3 style={{ margin: '0.25rem 0 0 0', fontSize: '1.25rem' }}>{examData.module_title}</h3>
              </div>
              <button onClick={() => setExamModalOpen(false)} style={{ background: 'transparent', color: '#94a3b8', fontSize: '1.2rem' }}>✕</button>
            </div>

            {/* Exam Results Screen */}
            {examResult ? (
              <div>
                <div style={{ padding: '1rem', borderRadius: '0.5rem', backgroundColor: examResult.passed ? '#064e3b' : '#450a0a', marginBottom: '1.5rem', textAlign: 'center' }}>
                  <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '1.3rem', color: examResult.passed ? '#4ade80' : '#f87171' }}>
                    {examResult.passed ? "Assessment Passed! 🎉" : "Assessment Not Passed"}
                  </h4>
                  <div style={{ fontSize: '2rem', fontWeight: 800 }}>{examResult.score_percentage}%</div>
                  <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.85rem' }}>{examResult.feedback_message}</p>
                </div>

                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '1rem' }}>Question Review & Explanations:</h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {examResult.answer_reviews.map((r, ri) => (
                      <div key={ri} style={{ padding: '0.75rem', backgroundColor: '#0f172a', borderRadius: '0.5rem', borderLeft: r.is_correct ? '4px solid #22c55e' : '4px solid #ef4444' }}>
                        <div style={{ fontWeight: 600, fontSize: '0.85rem', marginBottom: '0.35rem' }}>{ri + 1}. {r.text}</div>
                        <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                          Your Choice: <strong style={{ color: r.is_correct ? '#4ade80' : '#f87171' }}>{r.user_selected}</strong> &bull; Correct: <strong>{r.correct_option}</strong>
                        </div>
                        <div style={{ fontSize: '0.75rem', color: '#38bdf8', marginTop: '0.25rem' }}>
                          💡 <em>{r.explanation}</em>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <button 
                  onClick={() => setExamModalOpen(false)}
                  style={{ width: '100%', padding: '0.75rem', backgroundColor: '#0284c7', color: 'white', borderRadius: '0.5rem', fontWeight: 600 }}
                >
                  Return to Roadmap
                </button>
              </div>
            ) : (
              /* Ongoing Exam Questions Form */
              <form onSubmit={handleSubmitExam}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', marginBottom: '1.5rem' }}>
                  {examData.questions.map((q, qi) => (
                    <div key={q.id} style={{ padding: '1rem', backgroundColor: '#0f172a', borderRadius: '0.5rem' }}>
                      <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.75rem' }}>
                        Q{qi + 1}. {q.text}
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '0.5rem' }}>
                        {[
                          { key: 'A', text: q.option_a },
                          { key: 'B', text: q.option_b },
                          { key: 'C', text: q.option_c },
                          { key: 'D', text: q.option_d },
                        ].map(opt => (
                          <label key={opt.key} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.55rem 0.85rem', borderRadius: '0.4rem', border: '1px solid', borderColor: examAnswers[q.id] === opt.key ? '#0284c7' : '#334155', backgroundColor: examAnswers[q.id] === opt.key ? '#082f49' : '#1e293b', cursor: 'pointer', fontSize: '0.85rem' }}>
                            <input 
                              type="radio" 
                              name={`exam-q-${q.id}`} 
                              value={opt.key}
                              checked={examAnswers[q.id] === opt.key}
                              onChange={() => setExamAnswers({ ...examAnswers, [q.id]: opt.key })}
                              required
                            />
                            <span><strong>{opt.key}.</strong> {opt.text}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>

                <button 
                  type="submit" 
                  disabled={loading}
                  style={{ width: '100%', padding: '0.75rem', backgroundColor: '#22c55e', color: 'white', borderRadius: '0.5rem', fontWeight: 700, fontSize: '0.95rem' }}
                >
                  {loading ? "Submitting for Automatic Grading..." : "Submit Answers for Evaluation"}
                </button>
              </form>
            )}

          </div>
        </div>
      )}

      {/* ================= MODAL: AUTHENTICATION ================= */}
      {authModalOpen && (
        <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 60, padding: '1rem' }}>
          <div style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '0.75rem', width: '100%', maxWidth: '420px', padding: '1.5rem' }}>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h3 style={{ margin: 0, fontSize: '1.25rem' }}>
                {authMode === 'login' ? "Sign In to EduPath AI" : "Create Learner Account"}
              </h3>
              <button onClick={() => setAuthModalOpen(false)} style={{ background: 'transparent', color: '#94a3b8' }}>✕</button>
            </div>

            {/* Quick Demo Login Bar for Evaluators */}
            <div style={{ padding: '0.75rem', backgroundColor: '#0f172a', borderRadius: '0.5rem', marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.4rem', fontWeight: 600 }}>QUICK 1-CLICK DEMO LOGIN:</div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button 
                  onClick={() => { handleQuickLogin('student@edupath.ai', 'password123'); setAuthModalOpen(false); }}
                  style={{ flex: 1, padding: '0.4rem', backgroundColor: '#0369a1', color: 'white', borderRadius: '0.35rem', fontSize: '0.75rem', fontWeight: 600 }}
                >
                  Student Demo
                </button>
                <button 
                  onClick={() => { handleQuickLogin('admin@edupath.ai', 'admin123'); setAuthModalOpen(false); }}
                  style={{ flex: 1, padding: '0.4rem', backgroundColor: '#475569', color: 'white', borderRadius: '0.35rem', fontSize: '0.75rem', fontWeight: 600 }}
                >
                  Admin Demo
                </button>
              </div>
            </div>

            <form onSubmit={handleAuthSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              {authMode === 'register' && (
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Full Name</label>
                  <input 
                    type="text" 
                    placeholder="e.g. Mukesh Podugu" 
                    value={authForm.name} 
                    onChange={e => setAuthForm({ ...authForm, name: e.target.value })} 
                    required 
                    style={{ width: '100%' }}
                  />
                </div>
              )}

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Email Address</label>
                <input 
                  type="email" 
                  placeholder="learner@edupath.ai" 
                  value={authForm.email} 
                  onChange={e => setAuthForm({ ...authForm, email: e.target.value })} 
                  required 
                  style={{ width: '100%' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Password</label>
                <input 
                  type="password" 
                  placeholder="••••••••" 
                  value={authForm.password} 
                  onChange={e => setAuthForm({ ...authForm, password: e.target.value })} 
                  required 
                  style={{ width: '100%' }}
                />
              </div>

              {authMode === 'register' && (
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Role</label>
                  <select 
                    value={authForm.role} 
                    onChange={e => setAuthForm({ ...authForm, role: e.target.value })}
                    style={{ width: '100%' }}
                  >
                    <option value="student">Student / Learner</option>
                    <option value="admin">Administrator</option>
                  </select>
                </div>
              )}

              <button 
                type="submit" 
                disabled={loading}
                style={{ width: '100%', padding: '0.75rem', backgroundColor: '#0284c7', color: 'white', borderRadius: '0.5rem', fontWeight: 600, marginTop: '0.5rem' }}
              >
                {loading ? "Processing..." : (authMode === 'login' ? "Sign In" : "Register Account")}
              </button>
            </form>

            <div style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.8rem', color: '#94a3b8' }}>
              {authMode === 'login' ? (
                <span>Don't have an account? <a href="#register" onClick={() => setAuthMode('register')} style={{ color: '#38bdf8' }}>Register</a></span>
              ) : (
                <span>Already have an account? <a href="#login" onClick={() => setAuthMode('login')} style={{ color: '#38bdf8' }}>Sign In</a></span>
              )}
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
