import json
from sqlalchemy.orm import Session
from .models import (
    Career, Skill, CareerSkill, Prerequisite, Question, 
    LearningAction, LearningModule, LearningResource, 
    ModuleAssessment, SubscriptionPlan, User, LearnerProfile
)
from .auth import hash_password

def seed_data(db: Session):
    # Check if subscription plans already exist as a proxy for new seed
    if db.query(SubscriptionPlan).first() is not None:
        return

    print("Seeding extended EduPath AI database...")

    # 1. SUBSCRIPTION PLANS
    free_plan = SubscriptionPlan(
        code="free",
        name="Free Explorer",
        price_inr=0,
        billing_interval="lifetime",
        features_json=json.dumps([
            "1 Target Career Roadmap",
            "Core Learning Modules",
            "Module Assessments",
            "Next Best Learning Action (NBLA) recommendations",
            "Standard community resources"
        ])
    )
    prem_monthly = SubscriptionPlan(
        code="premium_monthly",
        name="Pro Learner (Monthly)",
        price_inr=499,
        billing_interval="month",
        features_json=json.dumps([
            "Unlimited Career Roadmaps",
            "Curated YouTube & Industry Resource Playlists",
            "Unlimited Exam Retakes with Deep Explanations",
            "Priority AI Learning Path Optimization",
            "Downloadable Career Readiness Reports",
            "Resume Skill Gap Parser"
        ])
    )
    prem_annual = SubscriptionPlan(
        code="premium_annual",
        name="Career Accelerator (Annual)",
        price_inr=3999,
        billing_interval="year",
        features_json=json.dumps([
            "Everything in Pro Learner",
            "Save 33% on annual subscription",
            "Exclusive End-to-End Capstone Projects",
            "Direct Mentor Portfolio Review",
            "Verified Certificate of Completion",
            "1-on-1 Interview Prep Roadmap"
        ])
    )
    db.add_all([free_plan, prem_monthly, prem_annual])
    db.commit()

    # 2. DEFAULT USERS (STUDENT & ADMIN)
    admin_user = db.query(User).filter(User.email == "admin@edupath.ai").first()
    if not admin_user:
        admin_user = User(
            name="System Administrator",
            email="admin@edupath.ai",
            password_hash=hash_password("admin123"),
            role="admin",
            is_email_verified=True,
            subscription_tier="premium_annual"
        )
        db.add(admin_user)

    student_user = db.query(User).filter(User.email == "student@edupath.ai").first()
    if not student_user:
        student_user = User(
            name="Mukesh Podugu",
            email="student@edupath.ai",
            password_hash=hash_password("password123"),
            role="student",
            is_email_verified=True,
            subscription_tier="free",
            study_streak_days=3,
            total_study_minutes=180
        )
        db.add(student_user)
        db.commit()
        db.refresh(student_user)

        # Profile for student
        profile = LearnerProfile(
            user_id=student_user.id,
            education_level="B.Tech Computer Science & Engineering",
            degree_major="Artificial Intelligence & Machine Learning",
            current_status="Student",
            technical_skills="Python, SQL, Basic Statistics, Git",
            soft_skills="Analytical Thinking, Problem Solving",
            certifications="Python for Everybody (Coursera)",
            projects_summary="Predictive Housing Price Model using Scikit-Learn",
            work_experience_years=0.5,
            study_hours_per_week=15,
            preferred_format="Interactive Labs & Video Playlists"
        )
        db.add(profile)
        db.commit()

    # 3. CAREERS
    mle = db.query(Career).filter(Career.name == "Machine Learning Engineer").first()
    if not mle:
        mle = Career(
            name="Machine Learning Engineer", 
            description="Designs, builds, and deploys high-performance machine learning models and end-to-end MLOps pipelines into production.",
            onet_soc_code="15-1251.00",
            typical_salary_range="₹9,00,000 - ₹28,00,000 / yr",
            market_growth_rate="+25% (Extremely High Demand)"
        )
        db.add(mle)

    fed = db.query(Career).filter(Career.name == "Frontend Developer").first()
    if not fed:
        fed = Career(
            name="Frontend Developer", 
            description="Builds modern, responsive, high-performance web applications using React, JavaScript, and scalable component architecture.",
            onet_soc_code="15-1254.00",
            typical_salary_range="₹6,00,000 - ₹18,00,000 / yr",
            market_growth_rate="+18% (Steady Growth)"
        )
        db.add(fed)

    ds = db.query(Career).filter(Career.name == "Data Scientist").first()
    if not ds:
        ds = Career(
            name="Data Scientist", 
            description="Extracts actionable business intelligence and creates predictive statistical algorithms from complex datasets.",
            onet_soc_code="15-2051.00",
            typical_salary_range="₹8,50,000 - ₹25,00,000 / yr",
            market_growth_rate="+23% (High Demand)"
        )
        db.add(ds)

    cde = db.query(Career).filter(Career.name == "Cloud & DevOps Engineer").first()
    if not cde:
        cde = Career(
            name="Cloud & DevOps Engineer", 
            description="Automates infrastructure, continuous integration, container orchestration, and cloud architecture on AWS/GCP.",
            onet_soc_code="15-1244.00",
            typical_salary_range="₹8,00,000 - ₹24,00,000 / yr",
            market_growth_rate="+20% (High Demand)"
        )
        db.add(cde)

    db.commit()

    # Set student target career
    if student_user and mle:
        student_user.target_career_id = mle.id
        db.commit()

    # 4. SKILLS
    skills_map = {
        "Python": {"cat": "Programming", "desc": "Foundational programming language for AI, data analytics, and backend microservices."},
        "Linear Algebra": {"cat": "Mathematics", "desc": "Matrix transformations, eigenvalues, and vector spaces essential for neural architectures."},
        "Statistics": {"cat": "Mathematics", "desc": "Probability, hypothesis testing, Bayesian reasoning, and descriptive metrics."},
        "Machine Learning": {"cat": "AI/ML", "desc": "Supervised, unsupervised algorithms, model validation, and loss optimization."},
        "Deep Learning": {"cat": "AI/ML", "desc": "Convolutional networks, transformers, backpropagation, and PyTorch/TensorFlow."},
        "MLOps": {"cat": "DevOps/AI", "desc": "Model serialization, monitoring, CI/CD pipelines, and Dockerized inference endpoints."},
        
        "HTML & CSS": {"cat": "Frontend", "desc": "Semantic markup, responsive layouts, CSS Flexbox, Grid, and design systems."},
        "JavaScript": {"cat": "Frontend", "desc": "Modern ES6+ syntax, asynchronous event loop, promises, and DOM manipulation."},
        "React": {"cat": "Frontend", "desc": "Component-driven user interfaces, React hooks, state management, and SPA routing."},
        "Web Architecture": {"cat": "Architecture", "desc": "HTTP protocols, REST APIs, CDN caching, state, and client-server lifecycles."},

        "Docker & Containers": {"cat": "DevOps", "desc": "Containerization, image building, multi-stage Dockerfiles, and container networking."},
        "Linux & Bash": {"cat": "DevOps", "desc": "Shell scripting, process management, permissions, and server administration."}
    }

    db_skills = {}
    for s_name, meta in skills_map.items():
        existing = db.query(Skill).filter(Skill.name == s_name).first()
        if not existing:
            existing = Skill(name=s_name, category=meta["cat"], description=meta["desc"])
            db.add(existing)
            db.commit()
            db.refresh(existing)
        db_skills[s_name] = existing

    # 5. CAREER-SKILL MAPPINGS (O*NET Aligned)
    def add_career_skill(c_id, s_id, req, imp):
        cs = db.query(CareerSkill).filter(CareerSkill.career_id == c_id, CareerSkill.skill_id == s_id).first()
        if not cs:
            db.add(CareerSkill(career_id=c_id, skill_id=s_id, required_mastery=req, importance=imp))

    # MLE Skills
    add_career_skill(mle.id, db_skills["Python"].id, 0.90, 0.95)
    add_career_skill(mle.id, db_skills["Linear Algebra"].id, 0.80, 0.80)
    add_career_skill(mle.id, db_skills["Statistics"].id, 0.85, 0.90)
    add_career_skill(mle.id, db_skills["Machine Learning"].id, 0.90, 1.00)
    add_career_skill(mle.id, db_skills["Deep Learning"].id, 0.80, 0.85)
    add_career_skill(mle.id, db_skills["MLOps"].id, 0.70, 0.75)

    # Frontend Developer Skills
    add_career_skill(fed.id, db_skills["HTML & CSS"].id, 0.95, 0.90)
    add_career_skill(fed.id, db_skills["JavaScript"].id, 0.95, 0.95)
    add_career_skill(fed.id, db_skills["React"].id, 0.90, 1.00)
    add_career_skill(fed.id, db_skills["Web Architecture"].id, 0.80, 0.80)

    # Data Scientist Skills
    add_career_skill(ds.id, db_skills["Python"].id, 0.90, 0.90)
    add_career_skill(ds.id, db_skills["Statistics"].id, 0.90, 1.00)
    add_career_skill(ds.id, db_skills["Linear Algebra"].id, 0.75, 0.75)
    add_career_skill(ds.id, db_skills["Machine Learning"].id, 0.85, 0.90)

    # Cloud & DevOps
    add_career_skill(cde.id, db_skills["Linux & Bash"].id, 0.90, 0.95)
    add_career_skill(cde.id, db_skills["Docker & Containers"].id, 0.90, 1.00)
    add_career_skill(cde.id, db_skills["Python"].id, 0.75, 0.70)
    add_career_skill(cde.id, db_skills["Web Architecture"].id, 0.85, 0.85)

    db.commit()

    # 6. PREREQUISITES (DAG)
    def add_prereq(parent_id, child_id):
        p = db.query(Prerequisite).filter(Prerequisite.parent_skill_id == parent_id, Prerequisite.child_skill_id == child_id).first()
        if not p:
            db.add(Prerequisite(parent_skill_id=parent_id, child_skill_id=child_id, dependency_type="STRICT"))

    add_prereq(db_skills["Python"].id, db_skills["Machine Learning"].id)
    add_prereq(db_skills["Statistics"].id, db_skills["Machine Learning"].id)
    add_prereq(db_skills["Linear Algebra"].id, db_skills["Deep Learning"].id)
    add_prereq(db_skills["Machine Learning"].id, db_skills["Deep Learning"].id)
    add_prereq(db_skills["Python"].id, db_skills["MLOps"].id)
    add_prereq(db_skills["Machine Learning"].id, db_skills["MLOps"].id)

    add_prereq(db_skills["HTML & CSS"].id, db_skills["React"].id)
    add_prereq(db_skills["JavaScript"].id, db_skills["React"].id)
    add_prereq(db_skills["React"].id, db_skills["Web Architecture"].id)

    add_prereq(db_skills["Linux & Bash"].id, db_skills["Docker & Containers"].id)

    db.commit()

    # 7. LEARNING MODULES & VERIFIED RESOURCES
    modules_data = [
        # MLE Roadmap
        {
            "career": mle,
            "skill": db_skills["Python"],
            "title": "Python for Data Science & AI",
            "desc": "Master clean Python syntax, list comprehensions, NumPy vectorization, and pandas data manipulation.",
            "order": 1,
            "duration": 180,
            "resources": [
                {
                    "title": "Python Programming Full Course (freeCodeCamp)",
                    "platform": "YouTube",
                    "url": "https://www.youtube.com/watch?v=rfscVS0vtbw",
                    "type": "Video Course",
                    "mins": 120,
                    "free": True,
                    "diff": "Beginner",
                    "reason": "Comprehensive industry-standard foundation covering syntax, functions, and OOP."
                },
                {
                    "title": "Official Python Tutorial Documentation",
                    "platform": "Official Docs",
                    "url": "https://docs.python.org/3/tutorial/",
                    "type": "Documentation",
                    "mins": 45,
                    "free": True,
                    "diff": "Beginner",
                    "reason": "Authoritative guide from the Python Software Foundation for reference."
                },
                {
                    "title": "Kaggle Python Micro-Course",
                    "platform": "Kaggle Learn",
                    "url": "https://www.kaggle.com/learn/python",
                    "type": "Interactive Lab",
                    "mins": 60,
                    "free": True,
                    "diff": "Beginner",
                    "reason": "Hands-on coding exercises tailored specifically to data manipulation."
                }
            ],
            "questions": [
                ("What is the time complexity of looking up a key in a standard Python dictionary on average?", "O(1)", "O(n)", "O(log n)", "O(n^2)", "A", "Python dictionaries utilize hash tables, giving average O(1) constant time lookups."),
                ("Which of the following creates a generator in Python rather than a list?", "(x*2 for x in range(10))", "[x*2 for x in range(10)]", "{x*2 for x in range(10)}", "tuple(x*2 for x in range(10))", "A", "Parentheses syntax creates a memory-efficient generator expression."),
                ("How does NumPy achieve significantly faster execution than native Python lists?", "Vectorized C-level memory contiguity and SIMD operations", "By skipping memory allocation completely", "By compiling code to JavaScript", "By using multi-threading on every addition", "A", "NumPy stores data in contiguous memory blocks with homogeneous types executed in optimized C routines.")
            ]
        },
        {
            "career": mle,
            "skill": db_skills["Statistics"],
            "title": "Probability & Inferential Statistics",
            "desc": "Foundational probability distributions, Bayes' Theorem, hypothesis testing, confidence intervals, and p-values.",
            "order": 2,
            "duration": 210,
            "resources": [
                {
                    "title": "Essence of Probability & Bayes Rule (3Blue1Brown)",
                    "platform": "YouTube",
                    "url": "https://www.youtube.com/watch?v=HZGCoVF3YvM",
                    "type": "Video Playlist",
                    "mins": 60,
                    "free": True,
                    "diff": "Beginner",
                    "reason": "Intuitive visual explanations of conditional probability and prior/posterior updates."
                },
                {
                    "title": "StatQuest: Probability & Distributions",
                    "platform": "YouTube",
                    "url": "https://www.youtube.com/watch?v=oI3hZJqXJuc",
                    "type": "Video Tutorial",
                    "mins": 90,
                    "free": True,
                    "diff": "Intermediate",
                    "reason": "Clear step-by-step mathematical walkthroughs of normal, binomial, and Poisson distributions."
                },
                {
                    "title": "Khan Academy Statistics & Probability",
                    "platform": "Khan Academy",
                    "url": "https://www.khanacademy.org/math/statistics-probability",
                    "type": "Interactive Course",
                    "mins": 120,
                    "free": True,
                    "diff": "Beginner",
                    "reason": "Interactive quizzes and practice sets covering variance, standard deviation, and tests."
                }
            ],
            "questions": [
                ("What does a p-value less than 0.05 signify in standard hypothesis testing?", "Evidence to reject the null hypothesis at the 5% significance level", "A 95% probability that the research hypothesis is false", "That the data contains 5% outliers", "That the experiment must be discarded", "A", "A p-value below alpha (0.05) indicates that observed results are statistically unlikely under the null hypothesis."),
                ("Which metric is most robust to extreme positive outliers in a heavily skewed income dataset?", "Median", "Mean", "Standard Deviation", "Variance", "A", "The median represents the 50th percentile and is invariant to extreme tail values unlike the mean.")
            ]
        },
        {
            "career": mle,
            "skill": db_skills["Linear Algebra"],
            "title": "Linear Algebra for Machine Learning",
            "desc": "Vectors, dot products, matrices, rank, determinants, eigenvalues, and SVD decomposition.",
            "order": 3,
            "duration": 180,
            "resources": [
                {
                    "title": "Essence of Linear Algebra (3Blue1Brown)",
                    "platform": "YouTube",
                    "url": "https://www.youtube.com/watch?v=fNk_zzaMoSs",
                    "type": "Video Playlist",
                    "mins": 90,
                    "free": True,
                    "diff": "Intermediate",
                    "reason": "Geometric interpretations of matrix transformations, determinant scaling, and eigenvectors."
                },
                {
                    "title": "MIT 18.06 Linear Algebra Lectures (Gilbert Strang)",
                    "platform": "MIT OpenCourseWare",
                    "url": "https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/",
                    "type": "Course",
                    "mins": 180,
                    "free": True,
                    "diff": "Intermediate",
                    "reason": "World-renowned academic foundations of four fundamental vector subspaces."
                }
            ],
            "questions": [
                ("What does it geometrically mean if two non-zero vectors have a dot product equal to zero?", "The vectors are orthogonal (perpendicular at 90 degrees)", "The vectors are parallel in opposite directions", "One vector has infinite magnitude", "The vectors lie in zero-dimensional space", "A", "The dot product is proportional to cos(theta); cos(90 deg) = 0, indicating orthogonality."),
                ("In Principal Component Analysis (PCA), what do the eigenvectors of the covariance matrix represent?", "Directions of maximum variance in the feature space", "The labels of the clusters", "The learning rate of the optimizer", "The degree of overfitting", "A", "Eigenvectors define the principal axes along which feature variance is maximized.")
            ]
        },
        {
            "career": mle,
            "skill": db_skills["Machine Learning"],
            "title": "Applied Machine Learning & Algorithms",
            "desc": "Supervised learning (Regression, Trees, Random Forests, SVMs) and unsupervised methods (K-Means, PCA).",
            "order": 4,
            "duration": 240,
            "resources": [
                {
                    "title": "Machine Learning Specialization (Andrew Ng)",
                    "platform": "Coursera",
                    "url": "https://www.coursera.org/specializations/machine-learning-introduction",
                    "type": "Course",
                    "mins": 180,
                    "free": False,
                    "diff": "Intermediate",
                    "reason": "Gold-standard curriculum explaining gradient descent, cost functions, and regularization."
                },
                {
                    "title": "Scikit-Learn Official User Guide",
                    "platform": "Official Docs",
                    "url": "https://scikit-learn.org/stable/user_guide.html",
                    "type": "Documentation",
                    "mins": 60,
                    "free": True,
                    "diff": "Intermediate",
                    "reason": "Clear implementation patterns, hyperparameter tuning, and cross-validation pipelines."
                }
            ],
            "questions": [
                ("What is the primary role of L2 regularization (Ridge regression)?", "Penalizing large weight magnitudes to prevent overfitting", "Zeroing out all features automatically", "Accelerating batch gradient descent", "Replacing missing data points", "A", "L2 penalty shrinks weights toward zero, reducing model variance and preventing overfitting."),
                ("When evaluating a model for cancer detection where missing a sick patient is catastrophic, which metric is prioritized?", "Recall (Sensitivity)", "Precision", "Accuracy", "Specificity", "A", "High Recall minimizes False Negatives (missing a true positive case).")
            ]
        },
        {
            "career": mle,
            "skill": db_skills["Deep Learning"],
            "title": "Deep Neural Networks & Architectures",
            "desc": "Backpropagation, activation functions, CNNs, Transformers, and PyTorch model implementation.",
            "order": 5,
            "duration": 300,
            "resources": [
                {
                    "title": "Neural Networks: Zero to Hero (Andrej Karpathy)",
                    "platform": "YouTube",
                    "url": "https://www.youtube.com/playlist?list=PLAqhIrjkxbuWI23v9cThsA9GvCAUhRvKZ",
                    "type": "Video Playlist",
                    "mins": 240,
                    "free": True,
                    "diff": "Advanced",
                    "reason": "Code-first derivation of backpropagation, micrograd, and GPT architectures."
                },
                {
                    "title": "PyTorch Official Deep Learning Tutorials",
                    "platform": "Official Docs",
                    "url": "https://pytorch.org/tutorials/",
                    "type": "Interactive Lab",
                    "mins": 90,
                    "free": True,
                    "diff": "Advanced",
                    "reason": "Tensors, autograd, torch.nn modules, and GPU acceleration."
                }
            ],
            "questions": [
                ("Why does the vanishing gradient problem occur when training deep networks with Sigmoid activations?", "Sigmoid derivatives saturate near 0 for extreme inputs, causing gradients to vanish during chain rule multiplication", "Sigmoid outputs values greater than 1", "Sigmoid cannot be computed on GPUs", "Sigmoid only works for linear models", "A", "Sigmoid's maximum derivative is 0.25; chaining multiple layers multiplies fractions, shrinking gradients to zero."),
                ("What mechanism allows Transformers to model long-range context efficiently unlike RNNs?", "Multi-head Self-Attention with parallel matrix computations", "Sequential recurrence unrolling", "Convolutional pooling kernels", "Batch normalization layers", "A", "Self-attention computes token-to-token similarity matrices in parallel without sequential bottlenecks.")
            ]
        },
        {
            "career": mle,
            "skill": db_skills["MLOps"],
            "title": "MLOps: Production Deployment & Monitoring",
            "desc": "FastAPI model serving, Docker containerization, data drift detection, and CI/CD pipelines.",
            "order": 6,
            "duration": 180,
            "resources": [
                {
                    "title": "Deploy Machine Learning Models with FastAPI & Docker",
                    "platform": "YouTube",
                    "url": "https://www.youtube.com/watch?v=h5wLuVDr0oc",
                    "type": "Video Tutorial",
                    "mins": 75,
                    "free": True,
                    "diff": "Advanced",
                    "reason": "Hands-on guide to containerizing inference servers and exposing REST endpoints."
                },
                {
                    "title": "Full Stack Deep Learning MLOps Course",
                    "platform": "Full Stack Deep Learning",
                    "url": "https://fullstackdeeplearning.com/",
                    "type": "Course",
                    "mins": 150,
                    "free": True,
                    "diff": "Advanced",
                    "reason": "Industry standards for experiment tracking, model registries, and data drift monitoring."
                }
            ],
            "questions": [
                ("What is 'Data Drift' in production machine learning systems?", "Statistical divergence between live input feature distributions and training data distributions over time", "A hard drive failure on the inference node", "A database connection timeout", "A change in Python library versions", "A", "Data drift occurs when real-world distributions shift, degrading model predictive performance."),
                ("Why is ONNX (Open Neural Network Exchange) commonly used in deployment pipelines?", "Provides a standardized format for cross-platform model inference optimization across different hardware runtimes", "It replaces the need for training data", "It encrypts model weights with blockchain", "It turns Python code into HTML", "A", "ONNX enables interoperability between frameworks like PyTorch and high-speed C++ runtimes like TensorRT.")
            ]
        },
        # Data Scientist Roadmap
        {
            "career": ds,
            "skill": db_skills["Python"],
            "title": "Python for Data Analysis",
            "desc": "Pandas, NumPy, and exploratory data analysis pipelines.",
            "order": 1,
            "duration": 180,
            "resources": [
                {
                    "title": "Data Analysis with Python (freeCodeCamp)",
                    "platform": "YouTube",
                    "url": "https://www.youtube.com/watch?v=r-uOLxNrNk8",
                    "type": "Video Course",
                    "mins": 120,
                    "free": True,
                    "diff": "Beginner",
                    "reason": "Complete data exploration workflows using Pandas and Matplotlib."
                }
            ],
            "questions": [
                ("Which pandas method returns summary statistics for numerical columns?", "describe()", "info()", "summary()", "stats()", "A", "df.describe() generates count, mean, std, quartiles, and min/max.")
            ]
        },
        {
            "career": ds,
            "skill": db_skills["Statistics"],
            "title": "Statistical Modeling & Hypothesis Testing",
            "desc": "A/B testing, regression analysis, confidence intervals, and parametric tests.",
            "order": 2,
            "duration": 200,
            "resources": [
                {
                    "title": "Practical Statistics for Data Scientists",
                    "platform": "Kaggle Learn",
                    "url": "https://www.kaggle.com/learn",
                    "type": "Interactive Lab",
                    "mins": 90,
                    "free": True,
                    "diff": "Intermediate",
                    "reason": "Hands-on statistical test evaluation and metrics."
                }
            ],
            "questions": [
                ("In an A/B test, what does Type I error represent?", "False positive (rejecting true null hypothesis)", "False negative", "Sample size error", "Measurement bias", "A", "Type I error occurs when a test detects an effect that is not actually present.")
            ]
        },
        {
            "career": ds,
            "skill": db_skills["Linear Algebra"],
            "title": "Matrix Computations for Analytics",
            "desc": "Dimensionality reduction, covariance matrices, and vector spaces.",
            "order": 3,
            "duration": 150,
            "resources": [
                {
                    "title": "Linear Algebra for Data Science",
                    "platform": "YouTube",
                    "url": "https://www.youtube.com/watch?v=fNk_zzaMoSs",
                    "type": "Video Playlist",
                    "mins": 80,
                    "free": True,
                    "diff": "Intermediate",
                    "reason": "Vector computations in multivariate data analysis."
                }
            ],
            "questions": [
                ("What does the rank of a matrix signify?", "Maximum number of linearly independent rows or columns", "The number of total entries", "The matrix determinant", "The inverse dimensions", "A", "Rank denotes linear independence and dimensionality.")
            ]
        },
        {
            "career": ds,
            "skill": db_skills["Machine Learning"],
            "title": "Predictive Modeling & Feature Engineering",
            "desc": "Feature selection, tree ensembles, XGBoost, and model validation.",
            "order": 4,
            "duration": 220,
            "resources": [
                {
                    "title": "Kaggle Intermediate Machine Learning",
                    "platform": "Kaggle Learn",
                    "url": "https://www.kaggle.com/learn/intermediate-machine-learning",
                    "type": "Interactive Lab",
                    "mins": 100,
                    "free": True,
                    "diff": "Intermediate",
                    "reason": "Missing values, categorical encoders, and gradient boosting."
                }
            ],
            "questions": [
                ("Why is cross-validation superior to a single train-test split?", "Reduces variance of performance estimation and uses all data for validation", "It makes model training 10x faster", "It eliminates the need for hyperparameters", "It allows using test data for fitting", "A", "K-fold cross-validation prevents split bias and ensures generalization.")
            ]
        },
        # Frontend Developer Roadmap
        {
            "career": fed,
            "skill": db_skills["HTML & CSS"],
            "title": "Semantic HTML & Responsive CSS",
            "desc": "Modern HTML5 tags, CSS Flexbox, Grid, and mobile-first responsiveness.",
            "order": 1,
            "duration": 150,
            "resources": [
                {
                    "title": "HTML and CSS Full Course (freeCodeCamp)",
                    "platform": "YouTube",
                    "url": "https://www.youtube.com/watch?v=mU6anWqZJcc",
                    "type": "Video Course",
                    "mins": 120,
                    "free": True,
                    "diff": "Beginner",
                    "reason": "Comprehensive introduction to responsive web design and layout."
                }
            ],
            "questions": [
                ("Which CSS layout model provides two-dimensional grid-based alignment?", "CSS Grid", "Flexbox", "Float", "Inline-block", "A", "CSS Grid is designed for 2D (rows and columns) layouts, whereas Flexbox is 1D.")
            ]
        },
        {
            "career": fed,
            "skill": db_skills["JavaScript"],
            "title": "Modern JavaScript (ES6+)",
            "desc": "Closures, async/await, DOM events, promises, and fetch API.",
            "order": 2,
            "duration": 180,
            "resources": [
                {
                    "title": "JavaScript Tutorial for Beginners (Traversy Media)",
                    "platform": "YouTube",
                    "url": "https://www.youtube.com/watch?v=hdI2bqOjy3c",
                    "type": "Video Tutorial",
                    "mins": 90,
                    "free": True,
                    "diff": "Beginner",
                    "reason": "Covers DOM manipulation, event listeners, and asynchronous promises."
                }
            ],
            "questions": [
                ("What does the Event Loop in JavaScript do?", "Monitors Call Stack and Task Queue, pushing callback tasks to the stack when empty", "Executes multi-threaded CPU tasks simultaneously", "Compiles JavaScript to assembly", "Handles database connections", "A", "The event loop coordinates asynchronous execution in JavaScript's single-threaded runtime.")
            ]
        },
        {
            "career": fed,
            "skill": db_skills["React"],
            "title": "React: Components, State & Hooks",
            "desc": "JSX, useState, useEffect, custom hooks, and component lifecycle.",
            "order": 3,
            "duration": 210,
            "resources": [
                {
                    "title": "React 18 Tutorial for Beginners (Codevolution)",
                    "platform": "YouTube",
                    "url": "https://www.youtube.com/watch?v=bMknfKXIFA8",
                    "type": "Video Playlist",
                    "mins": 120,
                    "free": True,
                    "diff": "Intermediate",
                    "reason": "Thorough breakdown of React hooks, context, and state management."
                }
            ],
            "questions": [
                ("Why must React state never be mutated directly?", "Direct mutations do not trigger re-render cycles and break virtual DOM diffing", "It causes syntax errors in JavaScript", "It deletes component props", "It resets the browser cache", "A", "Using setState ensures React schedules reconciliation and re-renders the UI.")
            ]
        },
        {
            "career": fed,
            "skill": db_skills["Web Architecture"],
            "title": "Web Performance & API Integration",
            "desc": "RESTful endpoints, HTTP headers, CDN caching, and bundling optimization.",
            "order": 4,
            "duration": 150,
            "resources": [
                {
                    "title": "MDN Web Architecture & HTTP Guide",
                    "platform": "Official Docs",
                    "url": "https://developer.mozilla.org/en-US/docs/Web/HTTP",
                    "type": "Documentation",
                    "mins": 60,
                    "free": True,
                    "diff": "Intermediate",
                    "reason": "In-depth reference for caching, CORS, and request-response security."
                }
            ],
            "questions": [
                ("Which HTTP status code indicates a successful resource creation?", "201 Created", "200 OK", "204 No Content", "301 Moved", "A", "201 Created specifically denotes that a new entity was created.")
            ]
        }
    ]

    for m_data in modules_data:
        mod = db.query(LearningModule).filter(
            LearningModule.career_id == m_data["career"].id,
            LearningModule.skill_id == m_data["skill"].id
        ).first()

        if not mod:
            mod = LearningModule(
                career_id=m_data["career"].id,
                skill_id=m_data["skill"].id,
                title=m_data["title"],
                description=m_data["desc"],
                order_index=m_data["order"],
                estimated_duration_minutes=m_data["duration"]
            )
            db.add(mod)
            db.commit()
            db.refresh(mod)

        # Assessment
        ass = db.query(ModuleAssessment).filter(ModuleAssessment.module_id == mod.id).first()
        if not ass:
            ass = ModuleAssessment(
                module_id=mod.id,
                title=f"{mod.title} Assessment",
                duration_minutes=15,
                pass_percentage=70.0
            )
            db.add(ass)
            db.commit()
            db.refresh(ass)

        # Resources
        for r_item in m_data["resources"]:
            existing_r = db.query(LearningResource).filter(
                LearningResource.module_id == mod.id,
                LearningResource.title == r_item["title"]
            ).first()
            if not existing_r:
                db.add(LearningResource(
                    module_id=mod.id,
                    skill_id=m_data["skill"].id,
                    title=r_item["title"],
                    platform=r_item["platform"],
                    url=r_item["url"],
                    resource_type=r_item["type"],
                    estimated_duration_minutes=r_item["mins"],
                    is_free=r_item["free"],
                    difficulty=r_item["diff"],
                    relevance_reason=r_item["reason"]
                ))

        # Questions
        for q_tuple in m_data["questions"]:
            text, a, b, c, d, corr, expl = q_tuple
            existing_q = db.query(Question).filter(Question.text == text).first()
            if not existing_q:
                db.add(Question(
                    assessment_id=ass.id,
                    skill_id=m_data["skill"].id,
                    text=text,
                    option_a=a,
                    option_b=b,
                    option_c=c,
                    option_d=d,
                    correct_option=corr,
                    explanation=expl
                ))
    # 8. SEED LEARNING ACTIONS FOR NBLA OPTIMIZER
    if db.query(LearningAction).count() == 0:
        for s_name, s_obj in db_skills.items():
            db.add_all([
                LearningAction(
                    title=f"Core Concepts & Video Guide: {s_name}",
                    description=f"Structured video lessons and core theoretical principles for {s_name}.",
                    skill_id=s_obj.id,
                    action_type="LEARN",
                    expected_gain=0.35,
                    learning_effort=35.0,
                    url=None
                ),
                LearningAction(
                    title=f"Interactive Practice Workshop: {s_name}",
                    description=f"Hands-on exercises and practical problem-solving for {s_name}.",
                    skill_id=s_obj.id,
                    action_type="PRACTICE",
                    expected_gain=0.25,
                    learning_effort=25.0,
                    url=None
                ),
                LearningAction(
                    title=f"Competency Evaluation Quiz: {s_name}",
                    description=f"Timed quiz assessing current mastery in {s_name}.",
                    skill_id=s_obj.id,
                    action_type="ASSESSMENT",
                    expected_gain=0.08,
                    learning_effort=15.0,
                    url=None
                ),
                LearningAction(
                    title=f"Applied Portfolio Project: {s_name}",
                    description=f"Design and implement a real-world capstone application covering {s_name}.",
                    skill_id=s_obj.id,
                    action_type="PROJECT",
                    expected_gain=0.55,
                    learning_effort=90.0,
                    url=None
                )
            ])
        db.commit()

    db.commit()
    print("Database seeding completed successfully.")
