import React, { useState, useEffect } from 'react';
import { 
  fetchCareers, onboardUser, submitDiagnostic, 
  fetchDashboard, completeAction 
} from './api';
import { 
  BookOpen, CheckCircle, Lock, PlayCircle, Star, 
  Target, Award, Clock, ArrowRight, ShieldAlert, Check
} from 'lucide-react';

export default function App() {
  // Navigation states: 'onboard' | 'quiz' | 'dashboard'
  const [view, setView] = useState('onboard');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Onboarding Form State
  const [careers, setCareers] = useState([]);
  const [name, setName] = useState('');
  const [selectedCareerId, setSelectedCareerId] = useState('');
  const [knownSkills, setKnownSkills] = useState([]); // List of skill IDs
  
  // Current user details
  const [userId, setUserId] = useState(null);
  
  // Diagnostic Quiz State
  const [quizQuestions, setQuizQuestions] = useState([]);
  const [quizAnswers, setQuizAnswers] = useState({}); // questionId -> selectedOption ('A'|'B'|'C'|'D')
  
  // Dashboard data
  const [dashboardData, setDashboardData] = useState(null);
  const [completingActionId, setCompletingActionId] = useState(null);
  const [assessmentScore, setAssessmentScore] = useState(85); // Simulated score slider value

  // Fetch initial careers
  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const data = await fetchCareers();
        setCareers(data);
        if (data.length > 0) {
          setSelectedCareerId(data[0].id.toString());
        }
      } catch (err) {
        setError("Could not load careers. Make sure the backend server is running on port 8000.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  // Filter skills based on selected career for onboarding checkboxes
  const getSkillsForSelectedCareer = () => {
    const career = careers.find(c => c.id.toString() === selectedCareerId);
    if (!career) return [];
    
    // In our backend seed, Machine Learning Engineer has specific skills, etc.
    // We map career names to their seed skill names for mock selection
    if (career.name.includes("Machine Learning")) {
      return [
        { id: 1, name: "Python" },
        { id: 2, name: "Linear Algebra" },
        { id: 3, name: "Statistics" },
        { id: 4, name: "Machine Learning" },
        { id: 5, name: "Deep Learning" },
        { id: 6, name: "MLOps" }
      ];
    } else if (career.name.includes("Frontend")) {
      return [
        { id: 7, name: "HTML & CSS" },
        { id: 8, name: "JavaScript" },
        { id: 9, name: "React" },
        { id: 10, name: "Web Architecture" }
      ];
    } else { // Data Scientist
      return [
        { id: 1, name: "Python" },
        { id: 3, name: "Statistics" },
        { id: 4, name: "Machine Learning" }
      ];
    }
  };

  const handleSkillCheck = (skillId) => {
    if (knownSkills.includes(skillId)) {
      setKnownSkills(knownSkills.filter(id => id !== skillId));
    } else {
      setKnownSkills([...knownSkills, skillId]);
    }
  };

  // Submit onboarding details
  const handleOnboard = async (e) => {
    e.preventDefault();
    if (!name.trim()) return alert("Please enter your name");
    
    try {
      setLoading(true);
      setError(null);
      const res = await onboardUser(name, parseInt(selectedCareerId), knownSkills);
      setUserId(res.user.id);
      
      if (res.questions && res.questions.length > 0) {
        setQuizQuestions(res.questions);
        setView('quiz');
      } else {
        // No prior skills selected or no questions available, skip directly to dashboard
        const dash = await fetchDashboard(res.user.id);
        setDashboardData(dash);
        setView('dashboard');
      }
    } catch (err) {
      setError(err.message || "Failed to onboard");
    } finally {
      setLoading(false);
    }
  };

  // Submit diagnostic quiz answers
  const handleQuizSubmit = async (e) => {
    e.preventDefault();
    
    // Format answers for API
    const formattedAnswers = Object.entries(quizAnswers).map(([qId, val]) => ({
      question_id: parseInt(qId),
      selected_option: val
    }));
    
    try {
      setLoading(true);
      setError(null);
      // 1. Submit diagnostic responses
      await submitDiagnostic(userId, formattedAnswers);
      // 2. Fetch updated dashboard
      const dash = await fetchDashboard(userId);
      setDashboardData(dash);
      setView('dashboard');
    } catch (err) {
      setError(err.message || "Failed to submit diagnostic quiz");
    } finally {
      setLoading(false);
    }
  };

  // Complete NBLA action
  const handleCompleteAction = async (actionId, type) => {
    try {
      setCompletingActionId(actionId);
      setError(null);
      
      // If it is an assessment, we can pass the simulated user score
      const score = type === "ASSESSMENT" ? (assessmentScore / 100) : null;
      
      const updatedDash = await completeAction(userId, actionId, score);
      setDashboardData(updatedDash);
    } catch (err) {
      setError(err.message || "Failed to complete action");
    } finally {
      setCompletingActionId(null);
    }
  };

  const getActionColor = (type) => {
    switch (type) {
      case "LEARN": return "#3b82f6"; // Blue
      case "PRACTICE": return "#10b981"; // Green
      case "ASSESSMENT": return "#8b5cf6"; // Purple
      case "PROJECT":
      case "MINI_PROJECT": return "#f59e0b"; // Orange
      default: return "#64748b";
    }
  };

  // Quick reset to start over
  const handleReset = () => {
    setName('');
    setKnownSkills([]);
    setQuizAnswers({});
    setUserId(null);
    setDashboardData(null);
    setView('onboard');
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem 1.5rem' }}>
      {/* Dynamic Embedded Styling */}
      <style>{`
        button { cursor: pointer; transition: all 0.2s ease; }
        button:hover { filter: brightness(0.95); }
        button:disabled { opacity: 0.6; cursor: not-allowed; }
        input[type="text"], select {
          width: 100%; padding: 0.75rem 1rem; border: 1px solid #cbd5e1;
          border-radius: 0.5rem; font-size: 1rem; background-color: white; outline: none;
        }
        input[type="text"]:focus, select:focus {
          border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
        }
        .card {
          background-color: white; border: 1px solid #e2e8f0;
          border-radius: 0.75rem; padding: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
      `}</style>

      {/* Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2.5rem', borderBottom: '1px solid #e2e8f0', paddingBottom: '1rem' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 700, color: '#1e293b', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '2rem' }}>🎯</span> SkillPath AI
          </h1>
          <p style={{ margin: '0.25rem 0 0 0', color: '#64748b', fontSize: '0.9rem' }}>
            Career-Aware Adaptive Learning Path Optimizer
          </p>
        </div>
        {view !== 'onboard' && (
          <button 
            onClick={handleReset} 
            style={{ padding: '0.5rem 1rem', backgroundColor: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: '0.5rem', fontSize: '0.85rem', color: '#475569', fontWeight: 500 }}
          >
            Restart Setup
          </button>
        )}
      </header>

      {error && (
        <div style={{ padding: '1rem', backgroundColor: '#fef2f2', border: '1px solid #fee2e2', color: '#b91c1c', borderRadius: '0.5rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <ShieldAlert size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* 1. ONBOARDING VIEW */}
      {view === 'onboard' && (
        <div style={{ maxWidth: '600px', margin: '0 auto' }} className="card">
          <h2 style={{ marginTop: 0, fontSize: '1.5rem', fontWeight: 600, color: '#0f172a', marginBottom: '1.5rem' }}>
            Start Your Learning Journey
          </h2>
          
          <form onSubmit={handleOnboard}>
            <div style={{ marginBottom: '1.25rem' }}>
              <label style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem', color: '#334155' }}>Your Name</label>
              <input 
                type="text" 
                placeholder="Enter your name" 
                value={name} 
                onChange={(e) => setName(e.target.value)} 
                required 
              />
            </div>

            <div style={{ marginBottom: '1.25rem' }}>
              <label style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem', color: '#334155' }}>Target Career / Role</label>
              <select 
                value={selectedCareerId} 
                onChange={(e) => {
                  setSelectedCareerId(e.target.value);
                  setKnownSkills([]); // clear skill ticks on career change
                }}
              >
                {careers.map(c => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>

            {selectedCareerId && (
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem', color: '#334155' }}>
                  Which of these skills do you already have basic knowledge in?
                </label>
                <p style={{ margin: '-0.25rem 0 0.75rem 0', fontSize: '0.85rem', color: '#64748b' }}>
                  We will generate a quick diagnostic exam for these skills to test your current mastery levels.
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  {getSkillsForSelectedCareer().map(s => (
                    <label 
                      key={s.id} 
                      style={{ 
                        display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem', 
                        border: '1px solid #e2e8f0', borderRadius: '0.5rem', cursor: 'pointer',
                        backgroundColor: knownSkills.includes(s.id) ? '#f0f7ff' : 'white',
                        borderColor: knownSkills.includes(s.id) ? '#3b82f6' : '#e2e8f0'
                      }}
                    >
                      <input 
                        type="checkbox" 
                        checked={knownSkills.includes(s.id)}
                        onChange={() => handleSkillCheck(s.id)}
                        style={{ cursor: 'pointer' }}
                      />
                      <span style={{ fontSize: '0.9rem', color: '#1e293b', fontWeight: 500 }}>{s.name}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            <button 
              type="submit" 
              disabled={loading}
              style={{ 
                width: '100%', padding: '0.75rem', backgroundColor: '#3b82f6', color: 'white', 
                border: 'none', borderRadius: '0.5rem', fontSize: '1rem', fontWeight: 600,
                display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem'
              }}
            >
              {loading ? "Loading..." : (knownSkills.length > 0 ? "Begin Diagnostic Exam" : "Generate Learning Path")}
              <ArrowRight size={18} />
            </button>
          </form>
        </div>
      )}

      {/* 2. DIAGNOSTIC QUIZ VIEW */}
      {view === 'quiz' && (
        <div style={{ maxWidth: '700px', margin: '0 auto' }} className="card">
          <div style={{ borderBottom: '1px solid #e2e8f0', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
            <span style={{ backgroundColor: '#f0fdf4', color: '#16a34a', padding: '0.25rem 0.5rem', borderRadius: '0.25rem', fontSize: '0.75rem', fontWeight: 600 }}>DIAGNOSTIC ASSESSMENT</span>
            <h2 style={{ marginTop: '0.5rem', marginBottom: '0.25rem', fontSize: '1.35rem', fontWeight: 600, color: '#0f172a' }}>
              Assess Your Prior Knowledge
            </h2>
            <p style={{ margin: 0, color: '#64748b', fontSize: '0.85rem' }}>
              Please answer the following questions to help us evaluate your starting knowledge state.
            </p>
          </div>

          <form onSubmit={handleQuizSubmit}>
            {quizQuestions.map((q, idx) => (
              <div key={q.id} style={{ marginBottom: '1.75rem', paddingBottom: '1.25rem', borderBottom: idx !== quizQuestions.length - 1 ? '1px dashed #e2e8f0' : 'none' }}>
                <p style={{ fontWeight: 600, fontSize: '0.95rem', color: '#1e293b', marginBottom: '0.75rem' }}>
                  Q{idx + 1}. {q.text}
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '0.5rem' }}>
                  {[
                    { key: 'A', text: q.option_a },
                    { key: 'B', text: q.option_b },
                    { key: 'C', text: q.option_c },
                    { key: 'D', text: q.option_d },
                  ].map(opt => (
                    <label 
                      key={opt.key} 
                      style={{ 
                        display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem 1rem', 
                        border: '1px solid #cbd5e1', borderRadius: '0.5rem', cursor: 'pointer',
                        backgroundColor: quizAnswers[q.id] === opt.key ? '#eff6ff' : 'white',
                        borderColor: quizAnswers[q.id] === opt.key ? '#3b82f6' : '#cbd5e1'
                      }}
                    >
                      <input 
                        type="radio" 
                        name={`q-${q.id}`} 
                        value={opt.key}
                        checked={quizAnswers[q.id] === opt.key}
                        onChange={() => setQuizAnswers({ ...quizAnswers, [q.id]: opt.key })}
                        style={{ cursor: 'pointer' }}
                        required
                      />
                      <span style={{ fontSize: '0.9rem', color: '#334155' }}>
                        <strong>{opt.key}.</strong> {opt.text}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            ))}

            <button 
              type="submit" 
              disabled={loading}
              style={{ 
                width: '100%', padding: '0.75rem', backgroundColor: '#10b981', color: 'white', 
                border: 'none', borderRadius: '0.5rem', fontSize: '1rem', fontWeight: 600 
              }}
            >
              {loading ? "Submitting Assessment..." : "Submit Diagnostic Exam"}
            </button>
          </form>
        </div>
      )}

      {/* 3. DASHBOARD VIEW */}
      {view === 'dashboard' && dashboardData && (
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '2rem', alignItems: 'start' }}>
          
          {/* Left Panel: Career Progress & Skills Grid */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            
            {/* Career readiness indicator */}
            <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
              <div style={{ position: 'relative', width: '100px', height: '100px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <svg width="100" height="100" viewBox="0 0 36 36" style={{ transform: 'rotate(-90deg)' }}>
                  <path
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="#e2e8f0"
                    strokeWidth="3.5"
                  />
                  <path
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="#10b981"
                    strokeDasharray={`${dashboardData.career_readiness * 100}, 100`}
                    strokeWidth="3.5"
                    strokeLinecap="round"
                  />
                </svg>
                <div style={{ position: 'absolute', fontSize: '1.25rem', fontWeight: 700, color: '#0f172a' }}>
                  {Math.round(dashboardData.career_readiness * 100)}%
                </div>
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '0.85rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Career Readiness Score
                </h3>
                <h2 style={{ margin: '0.25rem 0', fontSize: '1.4rem', fontWeight: 700, color: '#0f172a' }}>
                  {dashboardData.career_name}
                </h2>
                <p style={{ margin: 0, fontSize: '0.85rem', color: '#64748b' }}>
                  Calculated using importance weights and mastery gaps relative to role requirements.
                </p>
              </div>
            </div>

            {/* Skills mastery list */}
            <div className="card">
              <h3 style={{ marginTop: 0, marginBottom: '1.25rem', fontSize: '1.1rem', color: '#1e293b', fontWeight: 600 }}>
                Skills Profile Analysis
              </h3>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                {dashboardData.skills_states.map(s => {
                  const isMastered = s.mastery >= s.required_mastery;
                  const isLocked = s.mastery < 0.5 && dashboardData.next_best_action && 
                                   dashboardData.skills_states.some(other => {
                                     // Quick heuristic: If this skill has a prerequisite relationship in database
                                     // and the parent skill is far from met, it shows a lock.
                                     // (Calculated on backend and filtered from NBLA).
                                     return false; 
                                   });
                  
                  return (
                    <div key={s.skill_id} style={{ borderBottom: '1px solid #f1f5f9', paddingBottom: '1rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <div>
                          <span style={{ fontWeight: 600, color: '#0f172a', marginRight: '0.5rem' }}>{s.skill_name}</span>
                          <span style={{ fontSize: '0.75rem', color: '#64748b', backgroundColor: '#f1f5f9', padding: '0.15rem 0.4rem', borderRadius: '0.25rem' }}>
                            Req: {Math.round(s.required_mastery * 100)}%
                          </span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          {/* Importance Stars */}
                          <div style={{ display: 'flex', gap: '0.05rem', color: '#fbbf24' }}>
                            {Array.from({ length: 3 }).map((_, i) => (
                              <Star key={i} size={13} fill={s.importance * 3 > i ? '#fbbf24' : 'none'} strokeWidth={1.5} />
                            ))}
                          </div>
                          {/* Mastery Status Badge */}
                          {isMastered ? (
                            <span style={{ color: '#15803d', backgroundColor: '#f0fdf4', fontSize: '0.75rem', padding: '0.15rem 0.5rem', borderRadius: '9999px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.15rem' }}>
                              <CheckCircle size={10} /> Ready
                            </span>
                          ) : (
                            <span style={{ color: '#0369a1', backgroundColor: '#f0f9ff', fontSize: '0.75rem', padding: '0.15rem 0.5rem', borderRadius: '9999px', fontWeight: 600 }}>
                              Gap: {Math.round((s.required_mastery - s.mastery) * 100)}%
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Mastery Progress Bar */}
                      <div style={{ position: 'relative', width: '100%', height: '8px', backgroundColor: '#e2e8f0', borderRadius: '9999px', overflow: 'hidden' }}>
                        {/* Target Mastery Line */}
                        <div style={{ position: 'absolute', left: `${s.required_mastery * 100}%`, top: 0, width: '2px', height: '100%', backgroundColor: '#ef4444', zIndex: 10 }} title="Target Requirement" />
                        {/* Current Mastery Filled */}
                        <div style={{ width: `${s.mastery * 100}%`, height: '100%', backgroundColor: isMastered ? '#10b981' : '#3b82f6', borderRadius: '9999px' }} />
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem' }}>
                        <span>Current Mastery: {Math.round(s.mastery * 100)}%</span>
                        <span style={{ color: '#ef4444' }}>Target: {Math.round(s.required_mastery * 100)}%</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Prerequisite Node Graph Visualizer */}
            <div className="card">
              <h3 style={{ marginTop: 0, marginBottom: '0.25rem', fontSize: '1.1rem', color: '#1e293b', fontWeight: 600 }}>
                Prerequisite Dependency Network
              </h3>
              <p style={{ margin: '0 0 1.25rem 0', color: '#64748b', fontSize: '0.85rem' }}>
                Logical structure of curriculum dependencies. Unlocking foundational concepts activates downstream advanced topics.
              </p>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr 1fr', gap: '1rem', padding: '1rem', backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '0.5rem' }}>
                {/* Level 1: Foundational */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', justifyContent: 'center' }}>
                  <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#94a3b8', textAlign: 'center', textTransform: 'uppercase' }}>Foundational</div>
                  {dashboardData.skills_states.filter(s => ["Python", "Linear Algebra", "HTML & CSS", "JavaScript"].includes(s.skill_name)).map(s => {
                    const isCompleted = s.mastery >= s.required_mastery;
                    return (
                      <div key={s.skill_id} style={{ padding: '0.5rem', backgroundColor: isCompleted ? '#dcfce7' : '#dbeafe', border: '1px solid', borderColor: isCompleted ? '#86efac' : '#bfdbfe', borderRadius: '0.35rem', textAlign: 'center', fontSize: '0.8rem', fontWeight: 600, color: isCompleted ? '#166534' : '#1e40af' }}>
                        {s.skill_name}
                        <div style={{ fontSize: '0.65rem', fontWeight: 400, color: '#64748b' }}>{Math.round(s.mastery * 100)}%</div>
                      </div>
                    );
                  })}
                </div>

                {/* Flow Arrow Column */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', justifyContent: 'center' }}>
                  <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#94a3b8', textAlign: 'center', textTransform: 'uppercase' }}>Core Models / Library</div>
                  {dashboardData.skills_states.filter(s => ["Statistics", "Machine Learning", "React"].includes(s.skill_name)).map(s => {
                    const isCompleted = s.mastery >= s.required_mastery;
                    const parentsMet = s.skill_name === "Machine Learning" 
                      ? (dashboardData.skills_states.find(p => p.skill_name === "Python")?.mastery >= 0.5)
                      : true;
                    return (
                      <div key={s.skill_id} style={{ padding: '0.5rem', backgroundColor: isCompleted ? '#dcfce7' : parentsMet ? '#e0f2fe' : '#f1f5f9', border: '1px solid', borderColor: isCompleted ? '#86efac' : parentsMet ? '#bae6fd' : '#cbd5e1', borderRadius: '0.35rem', textAlign: 'center', fontSize: '0.8rem', fontWeight: 600, color: isCompleted ? '#166534' : parentsMet ? '#0369a1' : '#64748b' }}>
                        {!parentsMet && <Lock size={10} style={{ marginRight: '0.2rem', display: 'inline' }} />}
                        {s.skill_name}
                        <div style={{ fontSize: '0.65rem', fontWeight: 400, color: '#64748b' }}>{Math.round(s.mastery * 100)}%</div>
                      </div>
                    );
                  })}
                </div>

                {/* Level 3: Advanced */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', justifyContent: 'center' }}>
                  <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#94a3b8', textAlign: 'center', textTransform: 'uppercase' }}>Advanced & Deployment</div>
                  {dashboardData.skills_states.filter(s => ["Deep Learning", "MLOps", "Web Architecture"].includes(s.skill_name)).map(s => {
                    const isCompleted = s.mastery >= s.required_mastery;
                    const mlMastery = dashboardData.skills_states.find(p => p.skill_name === "Machine Learning")?.mastery || 0.0;
                    const reactMastery = dashboardData.skills_states.find(p => p.skill_name === "React")?.mastery || 0.0;
                    const parentsMet = s.skill_name === "Web Architecture" ? reactMastery >= 0.5 : mlMastery >= 0.5;
                    
                    return (
                      <div key={s.skill_id} style={{ padding: '0.5rem', backgroundColor: isCompleted ? '#dcfce7' : parentsMet ? '#fdf2f8' : '#f1f5f9', border: '1px solid', borderColor: isCompleted ? '#86efac' : parentsMet ? '#fbcfe8' : '#cbd5e1', borderRadius: '0.35rem', textAlign: 'center', fontSize: '0.8rem', fontWeight: 600, color: isCompleted ? '#166534' : parentsMet ? '#9d174d' : '#64748b' }}>
                        {!parentsMet && <Lock size={10} style={{ marginRight: '0.2rem', display: 'inline' }} />}
                        {s.skill_name}
                        <div style={{ fontSize: '0.65rem', fontWeight: 400, color: '#64748b' }}>{Math.round(s.mastery * 100)}%</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

          </div>

          {/* Right Panel: NBLA Recommendation */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            
            <div className="card" style={{ border: '2px solid #3b82f6', position: 'relative' }}>
              <div style={{ position: 'absolute', top: '-12px', left: '1.5rem', backgroundColor: '#3b82f6', color: 'white', padding: '0.15rem 0.75rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 600 }}>
                RECOMMENDED ACTION
              </div>
              
              {dashboardData.next_best_action ? (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginTop: '0.5rem', marginBottom: '1rem' }}>
                    <span style={{ 
                      backgroundColor: `${getActionColor(dashboardData.next_best_action.action.action_type)}15`,
                      color: getActionColor(dashboardData.next_best_action.action.action_type),
                      padding: '0.25rem 0.5rem', borderRadius: '0.25rem', fontSize: '0.75rem', fontWeight: 700
                    }}>
                      {dashboardData.next_best_action.action.action_type}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 500 }}>
                      Score: {dashboardData.next_best_action.action_score}
                    </span>
                  </div>

                  <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.2rem', fontWeight: 700, color: '#0f172a' }}>
                    {dashboardData.next_best_action.action.title}
                  </h3>
                  <p style={{ margin: '0 0 1.25rem 0', color: '#475569', fontSize: '0.9rem', lineHeight: 1.5 }}>
                    {dashboardData.next_best_action.action.description}
                  </p>

                  {/* Effort & Gain Badges */}
                  <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', padding: '0.75rem', backgroundColor: '#f8fafc', borderRadius: '0.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.8rem', color: '#475569' }}>
                      <Clock size={16} style={{ color: '#64748b' }} />
                      <span><strong>Effort:</strong> {dashboardData.next_best_action.action.learning_effort} mins</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.8rem', color: '#475569' }}>
                      <Award size={16} style={{ color: '#10b981' }} />
                      <span><strong>Expected Gain:</strong> +{Math.round(dashboardData.next_best_action.action.expected_gain * 100)}%</span>
                    </div>
                  </div>

                  {/* Optimizer Explanation */}
                  <div style={{ padding: '1rem', backgroundColor: '#eff6ff', border: '1px solid #dbeafe', borderRadius: '0.5rem', marginBottom: '1.5rem' }}>
                    <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.8rem', fontWeight: 700, color: '#1e40af', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      Optimizer Explainability Engine
                    </h4>
                    <p style={{ margin: 0, fontSize: '0.85rem', color: '#1e3a8a', lineHeight: 1.4, fontStyle: 'italic' }}>
                      {dashboardData.next_best_action.explanation.summary}
                    </p>

                    {/* Scoring factors breakdown */}
                    <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid #dbeafe' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#1e40af', marginBottom: '0.35rem' }}>Scoring Vector Breakdown:</div>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem', fontSize: '0.75rem', color: '#475569' }}>
                        <div>Gap Impact: <span style={{ fontWeight: 600 }}>+{dashboardData.next_best_action.explanation.components.gap_contribution}</span></div>
                        <div>Importance Impact: <span style={{ fontWeight: 600 }}>+{dashboardData.next_best_action.explanation.components.importance_contribution}</span></div>
                        <div>Prerequisite Impact: <span style={{ fontWeight: 600 }}>+{dashboardData.next_best_action.explanation.components.prerequisite_contribution}</span></div>
                        <div>Gain Impact: <span style={{ fontWeight: 600 }}>+{dashboardData.next_best_action.explanation.components.gain_contribution}</span></div>
                        <div style={{ color: '#b91c1c' }}>Effort Penalty: <span style={{ fontWeight: 600 }}>{dashboardData.next_best_action.explanation.components.effort_penalty}</span></div>
                      </div>
                    </div>
                  </div>

                  {/* Simulator scoring settings (Only if it's an assessment) */}
                  {dashboardData.next_best_action.action.action_type === "ASSESSMENT" && (
                    <div style={{ margin: '0 0 1rem 0', padding: '0.75rem', border: '1px dashed #8b5cf6', borderRadius: '0.5rem', backgroundColor: '#faf5ff' }}>
                      <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#6b21a8', marginBottom: '0.25rem' }}>
                        Simulate Assessment Exam Score: {assessmentScore}%
                      </label>
                      <input 
                        type="range" 
                        min="20" 
                        max="100" 
                        value={assessmentScore} 
                        onChange={(e) => setAssessmentScore(parseInt(e.target.value))}
                        style={{ width: '100%', cursor: 'pointer' }}
                      />
                    </div>
                  )}

                  {/* Perform Action Button */}
                  <button 
                    onClick={() => handleCompleteAction(dashboardData.next_best_action.action.id, dashboardData.next_best_action.action.action_type)}
                    disabled={completingActionId !== null}
                    style={{ 
                      width: '100%', padding: '0.75rem', backgroundColor: '#3b82f6', color: 'white', 
                      border: 'none', borderRadius: '0.5rem', fontSize: '0.95rem', fontWeight: 600,
                      display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem'
                    }}
                  >
                    {completingActionId ? "Processing..." : (
                      dashboardData.next_best_action.action.action_type === "ASSESSMENT" ? "Simulate Completing Assessment" : "Simulate Completing Study/Lab"
                    )}
                    <PlayCircle size={18} />
                  </button>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '2rem 0', color: '#16a34a' }}>
                  <Check size={40} style={{ margin: '0 auto 0.5rem auto' }} />
                  <h4 style={{ margin: 0, fontWeight: 700 }}>Path Completed!</h4>
                  <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.8rem', color: '#64748b' }}>
                    You have mastered all the required skills for this career role.
                  </p>
                </div>
              )}
            </div>

            {/* Platform instructions helper */}
            <div className="card" style={{ backgroundColor: '#f8fafc' }}>
              <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.85rem', color: '#475569', fontWeight: 600 }}>
                How Adaptive Learning Works:
              </h4>
              <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.8rem', color: '#64748b', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                <li>Completing study material incrementially improves skill mastery score.</li>
                <li>Simulating an exam evaluates and directly updates that skill's mastery percentage.</li>
                <li>When mastery states update, the NBLA Engine instantly re-runs the scoring matrix.</li>
                <li>Foundational skills are always prioritized first to unlock advanced downstream nodes.</li>
              </ul>
            </div>

          </div>

        </div>
      )}
    </div>
  );
}
