from sqlalchemy.orm import Session
from .models import Career, Skill, CareerSkill, Prerequisite, Question, LearningAction

def seed_data(db: Session):
    # Check if data already exists
    if db.query(Career).first() is not None:
        return  # Already seeded

    print("Seeding database...")

    # 1. Create Careers
    mle = Career(name="Machine Learning Engineer", description="Builds, deploys, and optimizes large-scale machine learning systems and pipelines.")
    fed = Career(name="Frontend Developer", description="Builds responsive, high-performance web applications using modern UI technologies.")
    ds = Career(name="Data Scientist", description="Analyzes complex data streams and creates predictive statistical models to drive decisions.")
    
    db.add_all([mle, fed, ds])
    db.commit()

    # 2. Create Skills
    skills_dict = {
        "Python": Skill(name="Python", description="Programming language widely used for machine learning, automation, and data analysis."),
        "Linear Algebra": Skill(name="Linear Algebra", description="Vectors, matrices, eigenvalues, and coordinate spaces underlying modern ML models."),
        "Statistics": Skill(name="Statistics", description="Probability, Bayesian reasoning, hypothesis testing, and statistical metrics."),
        "Machine Learning": Skill(name="Machine Learning", description="Supervised, unsupervised, model evaluation, and classical ML algorithms."),
        "Deep Learning": Skill(name="Deep Learning", description="Artificial neural networks, backpropagation, and deep architectures (CNNs, transformers)."),
        "MLOps": Skill(name="MLOps", description="Model deployment, CI/CD, data drift monitoring, and containerization (Docker/Kubernetes)."),
        
        "HTML & CSS": Skill(name="HTML & CSS", description="The fundamental building blocks of web pages, structural markup, and styling layouts."),
        "JavaScript": Skill(name="JavaScript", description="Dynamic scripting language for frontend interactive capabilities and asynchronous workflows."),
        "React": Skill(name="React", description="A popular component-based frontend library for building modern user interfaces."),
        "Web Architecture": Skill(name="Web Architecture", description="Client-server request-response lifecycles, HTTP methods, APIs, and CDN caching.")
    }
    
    for s in skills_dict.values():
        db.add(s)
    db.commit()

    # 3. Create Career-Skill mappings
    # Machine Learning Engineer Skills
    db.add_all([
        CareerSkill(career_id=mle.id, skill_id=skills_dict["Python"].id, required_mastery=0.90, importance=0.95),
        CareerSkill(career_id=mle.id, skill_id=skills_dict["Linear Algebra"].id, required_mastery=0.80, importance=0.80),
        CareerSkill(career_id=mle.id, skill_id=skills_dict["Statistics"].id, required_mastery=0.85, importance=0.90),
        CareerSkill(career_id=mle.id, skill_id=skills_dict["Machine Learning"].id, required_mastery=0.90, importance=1.00),
        CareerSkill(career_id=mle.id, skill_id=skills_dict["Deep Learning"].id, required_mastery=0.80, importance=0.85),
        CareerSkill(career_id=mle.id, skill_id=skills_dict["MLOps"].id, required_mastery=0.70, importance=0.75),
    ])
    
    # Frontend Developer Skills
    db.add_all([
        CareerSkill(career_id=fed.id, skill_id=skills_dict["HTML & CSS"].id, required_mastery=0.95, importance=0.90),
        CareerSkill(career_id=fed.id, skill_id=skills_dict["JavaScript"].id, required_mastery=0.95, importance=0.95),
        CareerSkill(career_id=fed.id, skill_id=skills_dict["React"].id, required_mastery=0.90, importance=1.00),
        CareerSkill(career_id=fed.id, skill_id=skills_dict["Web Architecture"].id, required_mastery=0.80, importance=0.80),
    ])

    # Data Scientist Skills
    db.add_all([
        CareerSkill(career_id=ds.id, skill_id=skills_dict["Python"].id, required_mastery=0.90, importance=0.90),
        CareerSkill(career_id=ds.id, skill_id=skills_dict["Statistics"].id, required_mastery=0.90, importance=1.00),
        CareerSkill(career_id=ds.id, skill_id=skills_dict["Machine Learning"].id, required_mastery=0.80, importance=0.80),
    ])
    db.commit()

    # 4. Create Prerequisites
    db.add_all([
        # ML / DS Path
        Prerequisite(parent_skill_id=skills_dict["Python"].id, child_skill_id=skills_dict["Machine Learning"].id),
        Prerequisite(parent_skill_id=skills_dict["Statistics"].id, child_skill_id=skills_dict["Machine Learning"].id),
        Prerequisite(parent_skill_id=skills_dict["Linear Algebra"].id, child_skill_id=skills_dict["Deep Learning"].id),
        Prerequisite(parent_skill_id=skills_dict["Machine Learning"].id, child_skill_id=skills_dict["Deep Learning"].id),
        Prerequisite(parent_skill_id=skills_dict["Python"].id, child_skill_id=skills_dict["MLOps"].id),
        Prerequisite(parent_skill_id=skills_dict["Machine Learning"].id, child_skill_id=skills_dict["MLOps"].id),
        
        # Frontend Path
        Prerequisite(parent_skill_id=skills_dict["HTML & CSS"].id, child_skill_id=skills_dict["React"].id),
        Prerequisite(parent_skill_id=skills_dict["JavaScript"].id, child_skill_id=skills_dict["React"].id),
        Prerequisite(parent_skill_id=skills_dict["React"].id, child_skill_id=skills_dict["Web Architecture"].id),
    ])
    db.commit()

    # 5. Create Questions
    # Python Questions
    db.add_all([
        Question(
            skill_id=skills_dict["Python"].id,
            text="What is the output of the following list comprehension: [x*2 for x in range(3)]?",
            option_a="[0, 2, 4]",
            option_b="[2, 4, 6]",
            option_c="[0, 1, 2]",
            option_d="[0, 2, 4, 6]",
            correct_option="A"
        ),
        Question(
            skill_id=skills_dict["Python"].id,
            text="Which of the following Python data structures is mutable?",
            option_a="Tuple",
            option_b="List",
            option_c="String",
            option_d="Integer",
            correct_option="B"
        ),
        Question(
            skill_id=skills_dict["Python"].id,
            text="What does the 'zip()' function in Python do?",
            option_a="Compresses a file to zip format",
            option_b="Aggregates elements from multiple iterables into tuples",
            option_c="Fast-iterates a single list",
            option_d="Deletes duplicates in lists",
            correct_option="B"
        )
    ])

    # Statistics Questions
    db.add_all([
        Question(
            skill_id=skills_dict["Statistics"].id,
            text="In probability, Bayes' theorem calculates which of the following?",
            option_a="Joint probability of independent events",
            option_b="Conditional probability P(A|B) given P(B|A)",
            option_c="Sum of standard deviations",
            option_d="Arithmetic mean of normal distribution",
            correct_option="B"
        ),
        Question(
            skill_id=skills_dict["Statistics"].id,
            text="Which metric is least affected by extreme outliers in a numerical dataset?",
            option_a="Mean",
            option_b="Median",
            option_c="Standard Deviation",
            option_d="Variance",
            correct_option="B"
        )
    ])

    # Linear Algebra Questions
    db.add_all([
        Question(
            skill_id=skills_dict["Linear Algebra"].id,
            text="What does a dot product of zero between two non-zero vectors signify?",
            option_a="The vectors are parallel",
            option_b="The vectors are orthogonal (perpendicular)",
            option_c="The vectors are collinear",
            option_d="One vector is a scalar multiple of the other",
            correct_option="B"
        ),
        Question(
            skill_id=skills_dict["Linear Algebra"].id,
            text="What is an eigenvector of a matrix A?",
            option_a="A vector that becomes zero when multiplied by A",
            option_b="A vector whose direction does not change when multiplied by A",
            option_c="A vector containing only eigenvalues",
            option_d="The inverse of vector A",
            correct_option="B"
        )
    ])

    # Machine Learning Questions
    db.add_all([
        Question(
            skill_id=skills_dict["Machine Learning"].id,
            text="What is overfitting in a machine learning model?",
            option_a="Model performs well on training data but poorly on unseen test data",
            option_b="Model performs poorly on both training and test data",
            option_c="Model parameters are too small to train",
            option_d="The dataset has too many labels",
            correct_option="A"
        ),
        Question(
            skill_id=skills_dict["Machine Learning"].id,
            text="Which model evaluation metric should be prioritized when false positives are highly costly?",
            option_a="Recall",
            option_b="Precision",
            option_c="Accuracy",
            option_d="F1-score",
            correct_option="B"
        )
    ])

    # HTML & CSS Questions
    db.add_all([
        Question(
            skill_id=skills_dict["HTML & CSS"].id,
            text="In CSS flexbox, which property controls alignment along the main axis?",
            option_a="align-items",
            option_b="justify-content",
            option_c="flex-wrap",
            option_d="align-content",
            correct_option="B"
        ),
        Question(
            skill_id=skills_dict["HTML & CSS"].id,
            text="Which CSS selector has the highest specificity?",
            option_a="div",
            option_b=".my-class",
            option_c="#my-id",
            option_d="div p",
            correct_option="C"
        )
    ])

    # JavaScript Questions
    db.add_all([
        Question(
            skill_id=skills_dict["JavaScript"].id,
            text="What is a closure in JavaScript?",
            option_a="A function combined with its lexical environment, allowing access to outer scope variables",
            option_b="The process of closing a browser window using scripts",
            option_c="An API endpoint termination block",
            option_d="An array filtering method",
            correct_option="A"
        ),
        Question(
            skill_id=skills_dict["JavaScript"].id,
            text="Which statement correctly describes 'Promises' in JavaScript?",
            option_a="They execute code only on multi-threaded CPUs",
            option_b="They represent the eventual completion or failure of an asynchronous operation",
            option_c="They are alternative syntax for loop declarations",
            option_d="They convert JSON strings to arrays synchronously",
            correct_option="B"
        )
    ])
    db.commit()

    # 6. Create Learning Actions
    # Python
    db.add_all([
        LearningAction(title="Python Syntax & Basics Guide", description="Learn syntax, variables, lists, and functions in Python.", skill_id=skills_dict["Python"].id, action_type="LEARN", expected_gain=0.40, learning_effort=30),
        LearningAction(title="Object-Oriented Python Practice", description="Practice defining classes, modules, and error-handling in Python.", skill_id=skills_dict["Python"].id, action_type="PRACTICE", expected_gain=0.25, learning_effort=25),
        LearningAction(title="Python Advanced Scripting Assessment", description="Take a comprehensive assessment on generators, decorators, and list comprehensions.", skill_id=skills_dict["Python"].id, action_type="ASSESSMENT", expected_gain=0.08, learning_effort=15)
    ])

    # Statistics
    db.add_all([
        LearningAction(title="Introduction to Probability & Descriptive Statistics", description="Understand distributions, mean, median, variances, and standard deviations.", skill_id=skills_dict["Statistics"].id, action_type="LEARN", expected_gain=0.35, learning_effort=40),
        LearningAction(title="Bayesian Inference & Hypothesis Testing Lab", description="Complete statistical labs testing confidence intervals and Bayes' Theorem.", skill_id=skills_dict["Statistics"].id, action_type="PRACTICE", expected_gain=0.25, learning_effort=35),
        LearningAction(title="Descriptive Statistics Quiz", description="Complete a quick 10-question evaluation on standard deviation and probability.", skill_id=skills_dict["Statistics"].id, action_type="ASSESSMENT", expected_gain=0.05, learning_effort=15)
    ])

    # Linear Algebra
    db.add_all([
        LearningAction(title="Matrix Algebra & Vectors Bootcamp", description="Study matrix multiplication, determinants, and vector transformations.", skill_id=skills_dict["Linear Algebra"].id, action_type="LEARN", expected_gain=0.35, learning_effort=45),
        LearningAction(title="Eigenvalues & Eigenvectors Visualization", description="Practice calculating transformations and eigenvalues interactively.", skill_id=skills_dict["Linear Algebra"].id, action_type="PRACTICE", expected_gain=0.20, learning_effort=20)
    ])

    # Machine Learning
    db.add_all([
        LearningAction(title="Supervised Learning Algorithms Video Course", description="Study Linear Regression, Decision Trees, SVMs, and logistic models.", skill_id=skills_dict["Machine Learning"].id, action_type="LEARN", expected_gain=0.35, learning_effort=50),
        LearningAction(title="Scikit-Learn Model Training Workshop", description="Implement and train classification and regression algorithms on practice datasets.", skill_id=skills_dict["Machine Learning"].id, action_type="PRACTICE", expected_gain=0.25, learning_effort=40),
        LearningAction(title="Predictive Pricing Model Mini-Project", description="Build a project to predict housing prices using regularization techniques.", skill_id=skills_dict["Machine Learning"].id, action_type="MINI_PROJECT", expected_gain=0.50, learning_effort=90),
    ])

    # Deep Learning
    db.add_all([
        LearningAction(title="Neural Network Architectures & Backpropagation", description="Understand fully connected layers, weights, activation functions, and gradient descent.", skill_id=skills_dict["Deep Learning"].id, action_type="LEARN", expected_gain=0.30, learning_effort=60),
        LearningAction(title="CNN Image Classifier Project", description="Build and train a Convolutional Neural Network from scratch in PyTorch to categorize CIFAR-10 images.", skill_id=skills_dict["Deep Learning"].id, action_type="PROJECT", expected_gain=0.60, learning_effort=120)
    ])

    # MLOps
    db.add_all([
        LearningAction(title="Model Serialization & FastAPI Deployment", description="Serialize Python model objects and expose inference endpoints using FastAPI.", skill_id=skills_dict["MLOps"].id, action_type="LEARN", expected_gain=0.30, learning_effort=45),
        LearningAction(title="CI/CD Pipeline & Dockerization Practice", description="Create docker containers for ML models and automate deployments with github actions.", skill_id=skills_dict["MLOps"].id, action_type="PRACTICE", expected_gain=0.25, learning_effort=35)
    ])

    # HTML & CSS
    db.add_all([
        LearningAction(title="Semantic HTML & CSS Flexbox Guide", description="Master structuring layout flows using modern flex containers.", skill_id=skills_dict["HTML & CSS"].id, action_type="LEARN", expected_gain=0.45, learning_effort=25)
    ])

    # JavaScript
    db.add_all([
        LearningAction(title="Modern JS, ES6 Syntax, & Async Callbacks", description="Master closures, promises, event listeners, and ES6 array methods.", skill_id=skills_dict["JavaScript"].id, action_type="LEARN", expected_gain=0.40, learning_effort=30),
        LearningAction(title="Fetch API & DOM Manipulation Lab", description="Build a weather widget contacting public endpoints.", skill_id=skills_dict["JavaScript"].id, action_type="PRACTICE", expected_gain=0.25, learning_effort=25)
    ])

    # React
    db.add_all([
        LearningAction(title="React Hooks, State & Props Fundamentals", description="Study state management, props, and side effects using useEffect.", skill_id=skills_dict["React"].id, action_type="LEARN", expected_gain=0.35, learning_effort=40),
        LearningAction(title="Single Page Portfolio App Project", description="Create an interactive portfolio router project.", skill_id=skills_dict["React"].id, action_type="MINI_PROJECT", expected_gain=0.55, learning_effort=80)
    ])

    # Web Architecture
    db.add_all([
        LearningAction(title="RESTful Web Services & CDN Caching", description="Understand status codes, cookies, sessions, and request-response cycles.", skill_id=skills_dict["Web Architecture"].id, action_type="LEARN", expected_gain=0.35, learning_effort=45)
    ])
    
    db.commit()
    print("Database seeding completed.")
