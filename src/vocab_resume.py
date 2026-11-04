import itertools

# ---------- skills (all tagged SKILL when they appear in the skills section) ----------
SKILLS = [
    "Python", "Java", "C", "C++", "C#", "JavaScript", "TypeScript", "Go", "Rust", "Kotlin",
    "Swift", "R", "MATLAB", "Scala", "PHP", "Ruby", "Dart", "Bash", "SQL", "PL/SQL",
    "HTML", "CSS", "React", "Angular", "Vue.js", "Next.js", "Node.js", "Express.js", "Django",
    "Flask", "FastAPI", "Spring Boot", "Tailwind CSS", "Bootstrap", "jQuery", "Redux",
    "MySQL", "PostgreSQL", "MongoDB", "SQLite", "Redis", "Firebase", "Oracle DB", "Cassandra",
    "NumPy", "Pandas", "Matplotlib", "Seaborn", "Scikit-learn", "TensorFlow", "Keras", "PyTorch",
    "XGBoost", "LightGBM", "OpenCV", "NLTK", "spaCy", "Hugging Face", "LangChain", "SHAP",
    "Optuna", "Streamlit", "Gradio", "Jupyter", "Tableau", "Power BI", "Excel", "Apache Spark",
    "Hadoop", "Kafka", "Airflow", "Docker", "Kubernetes", "Git", "GitHub", "GitLab", "Linux",
    "Jenkins", "Terraform", "AWS", "Microsoft Azure", "Google Cloud Platform", "Heroku",
    "Vercel", "Nginx", "Postman", "VS Code", "Figma", "Arduino", "Raspberry Pi", "ESP32",
    "Flutter", "React Native", "Android Studio", "Unity", "Blender", "Selenium", "JUnit",
    "Pytest", "REST APIs", "GraphQL", "WebSockets", "Machine Learning", "Deep Learning",
    "Natural Language Processing", "Computer Vision", "Data Structures and Algorithms",
    "Object-Oriented Programming", "Operating Systems", "DBMS", "Computer Networks",
    "Data Analysis", "Data Visualization", "Feature Engineering", "Prompt Engineering",
    "Transfer Learning", "CNN", "Cross-Validation", "Hyperparameter Tuning", "Ollama",
    "Agile", "Scrum", "Problem Solving", "Communication", "Teamwork", "Leadership",
]

SKILL_SECTION_HEADERS = ["Skills", "Technical Skills", "TECHNICAL SKILLS", "Key Skills",
                         "Skills & Tools", "Core Competencies", "SKILLS", "Tech Stack"]
SKILL_CATEGORY_LABELS = ["Languages", "Frameworks", "Tools", "Libraries", "Databases",
                         "Cloud", "Concepts", "Programming", "Web", "ML/AI"]

# ---------- degrees and branches (surface forms the generator may write) ----------
# canonical degree -> surface forms
DEGREES = {
    "B.Tech": ["B.Tech", "B.Tech.", "BTech", "B Tech", "Bachelor of Technology"],
    "B.E.": ["B.E.", "B.E", "BE", "Bachelor of Engineering"],
    "BCA": ["BCA", "Bachelor of Computer Applications"],
    "B.Sc": ["B.Sc", "B.Sc.", "BSc", "Bachelor of Science"],
    "M.Tech": ["M.Tech", "M.Tech.", "MTech", "Master of Technology"],
    "MCA": ["MCA", "Master of Computer Applications"],
}

# canonical branch -> surface forms
BRANCHES = {
    "CSE": ["Computer Science and Engineering", "Computer Science & Engineering", "CSE",
            "Computer Science", "Computer Science Engineering"],
    "ECE": ["Electronics and Communication Engineering", "Electronics & Communication Engineering",
            "ECE", "Electronics and Communication"],
    "EEE": ["Electrical and Electronics Engineering", "EEE", "Electrical & Electronics Engineering"],
    "MECH": ["Mechanical Engineering", "Mechanical", "MECH"],
    "CIVIL": ["Civil Engineering", "Civil"],
    "IT": ["Information Technology", "IT"],
    "AIML": ["Artificial Intelligence and Machine Learning", "CSE (AI & ML)", "CSE (AIML)",
             "Computer Science and Engineering (AI/ML)", "AI & ML", "AIML"],
    "AIDS": ["Artificial Intelligence and Data Science", "AI&DS", "CSE (AI & DS)", "AI & DS"],
}

# which branch can go with which degree
VALID_COMBOS = {
    "B.Tech": list(BRANCHES), "B.E.": list(BRANCHES),
    "M.Tech": ["CSE", "ECE", "EEE", "MECH", "CIVIL", "IT", "AIML"],
    "BCA": [None], "MCA": [None],
    "B.Sc": ["Computer Science", "Data Science", "Mathematics", "Physics", "Statistics"],
}

DEGREE_BRANCH_COMBOS = [
    (d, b) for d, branches in VALID_COMBOS.items() for b in branches
]

# ---------- companies (always O) ----------
COMPANIES = [
    "Infosys", "TCS", "Wipro", "HCLTech", "Tech Mahindra", "Cognizant", "Accenture", "Capgemini",
    "Deloitte", "Amazon", "Microsoft", "Google", "Adobe", "Oracle", "SAP Labs", "Cisco",
    "Intel", "NVIDIA", "Qualcomm", "Samsung R&D", "Bosch", "Siemens", "Honeywell", "Flipkart",
    "Swiggy", "Zomato", "Paytm", "PhonePe", "Razorpay", "Freshworks", "Zoho", "Juspay",
    "Cred", "Meesho", "Ola", "Byju's", "Unacademy", "Myntra", "Walmart Global Tech",
    "Goldman Sachs", "JP Morgan", "Morgan Stanley", "Mastercard", "Visa", "Atlassian",
    "ThoughtWorks", "Mindtree", "LTIMindtree", "Mphasis", "Hexaware", "Persistent Systems",
    "Zensar", "Cyient", "Tata Elxsi", "L&T Technology Services", "ISRO", "DRDO", "SanDisk",
    "Western Digital", "Dell Technologies", "HP Inc", "IBM", "Salesforce", "ServiceNow",
    "Tata Consultancy Services", "AI Startup Labs", "NeuralWorks Technologies",
    "BrightPath Solutions", "CodeCraft Pvt Ltd", "Nimbus Cloud Services",
]

# ---------- schools (always O; 10th/12th) ----------
SCHOOL_PREFIXES = [
    "Delhi Public School", "Kendriya Vidyalaya", "Narayana Junior College", "Sri Chaitanya",
    "Ryan International School", "St. Mary's High School", "DAV Public School",
    "Bhashyam Public School", "Little Flower Junior College", "Vidya Bharati School",
    "Army Public School", "Jawahar Navodaya Vidyalaya", "National Public School",
    "Oxford Public School", "Loyola Academy", "Montessori High School", "Sacred Heart School",
    "Gayatri Vidya Parishad School", "Sri Gayatri Educational Institutions",
    "FIITJEE Junior College", "Resonance Junior College", "Glendale Academy",
]
SCHOOL_PLACES = ["Hyderabad", "Vijayawada", "Chennai", "Bengaluru", "Pune", "Kolkata", "Guntur",
                 "Nagpur", "Jaipur", "Lucknow", "Vizag", "Coimbatore", "Mysuru", "Indore"]
SCHOOLS = [f"{p}, {c}" for p in SCHOOL_PREFIXES for c in SCHOOL_PLACES[:4]] + SCHOOL_PREFIXES

# ---------- project titles (always O) ----------
_PROJECT_KINDS = [
    "Student Attendance System", "Sentiment Analysis Engine", "Crop Disease Detector",
    "Smart Parking Manager", "Resume Screening Tool", "Stock Price Predictor",
    "Face Recognition Door Lock", "Chat Application", "E-Commerce Web App",
    "Expense Tracker", "Library Management System", "Traffic Sign Classifier",
    "Fake News Detector", "Weather Dashboard", "Hospital Appointment Portal",
    "Movie Recommendation System", "Voice Assistant", "Plagiarism Checker",
    "Home Automation Hub", "Quiz Platform", "Fitness Tracker App", "Job Portal",
    "Customer Churn Predictor", "Handwritten Digit Recognizer", "Portfolio Website",
    "Blood Donation Finder", "Food Delivery App", "Smart Irrigation System",
]
_PROJECT_STYLES = ["{}", "Smart {}", "{} using Machine Learning", "AI-Powered {}", "{} with Flask"]
PROJECT_TITLES = sorted({s.format(k) for k in _PROJECT_KINDS for s in _PROJECT_STYLES})

PROJECT_BULLET_TEMPLATES = [
    "Built a {kind} using {skill} and {skill2}",
    "Developed and deployed a {kind}; reduced manual effort by {n}%",
    "Implemented {skill} pipeline achieving {n}% accuracy",
    "Designed REST APIs with {skill} and integrated {skill2}",
    "Collaborated in a team of {t} to deliver the {kind}",
    "Optimized performance by {n}% using {skill}",
]
ROLE_TITLES = ["Software Engineering Intern", "Data Science Intern", "Machine Learning Intern",
               "Web Development Intern", "Research Intern", "Technical Content Intern",
               "Core Team Member", "Technical Lead", "Event Coordinator", "Student Volunteer",
               "Marketing Head", "Sub Team Lead", "Associate", "Teaching Assistant"]
CLUBS = ["Coding Club", "Robotics Club", "Entrepreneurship Club", "Microsoft Student Chapter",
         "Google Developer Student Club", "IEEE Student Branch", "NSS", "Photography Club",
         "Cultural Committee", "ACM Student Chapter", "Open Source Club", "Hackathon Cell"]

TARGET_ROLES = ["AI Engineer", "ML Engineer", "Data Analyst", "Data Scientist",
                "Software Developer", "Backend Developer", "Frontend Developer",
                "Full Stack Developer", "DevOps Engineer", "Cloud Engineer", "QA Engineer"]

if __name__ == "__main__":
    def dups(items):
        seen, d = set(), []
        for x in items:
            if x.lower() in seen:
                d.append(x)
            seen.add(x.lower())
        return d

    print("skills        :", len(SKILLS), "(need 100+)")
    print("companies     :", len(COMPANIES))
    print("schools       :", len(SCHOOLS))
    print("project titles:", len(PROJECT_TITLES))
    print("degree x branch combos:", len(DEGREE_BRANCH_COMBOS))
    print("duplicate skills   :", dups(SKILLS))
    print("duplicate companies:", dups(COMPANIES))
    print("duplicate schools  :", dups(SCHOOLS))

    from src.vocab_people_places import COLLEGES
    college_names = {n.lower() for n, _ in COLLEGES} | {s.lower() for _, s in COLLEGES}
    clash = [x for x in COMPANIES + SCHOOLS + PROJECT_TITLES if x.lower() in college_names]
    print("negatives that clash with college names:", clash)
    skill_clash = [x for x in COMPANIES if x.lower() in {s.lower() for s in SKILLS}]
    print("companies that clash with skills       :", skill_clash)