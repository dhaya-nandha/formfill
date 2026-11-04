import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "phrasebank"
OUT.mkdir(parents=True, exist_ok=True)

BANK = {
    "full_name": [
        "Full Name", "Name", "Your Name", "Candidate Name", "Name of the Candidate",
        "Name of applicant", "Applicant Name", "Full name (as per college ID)",
        "Full name as per records", "Enter your full name", "What is your name?",
        "Student Name", "Name of the student", "Participant Name",
        "Name (in capital letters)", "Your full name", "First and last name",
        "Complete name", "Name of the participant", "Candidate's full name",
        "Full Name (First Middle Last)", "Please tell us your name", "Applicant's name",
        "Name as on ID card", "Your good name", "Name of Applicant (in block letters)",
        "Full legal name", "Name of the intern applicant", "Registrant name",
        "Contact person name", "Your name please", "Name of the team leader",
        "Full Name of the Candidate", "Student's full name", "Enter name",
        "Name (as in college records)", "What should we call you? (full name)",
        "Name of the Participant (Full)", "Candidate name as per ID proof", "Name in full",
    ],
    "email": [
        "Email", "Email ID", "E-mail", "Email Address", "Your email", "Mail ID",
        "Mail address", "Email id (active)", "Official email address",
        "Personal Email ID", "Enter your email address", "Your email address",
        "Email (Gmail preferred)", "Valid email address", "Email Id for communication",
        "Contact email", "Student email", "College email ID", "Candidate email",
        "Applicant's email address", "Primary email", "Please provide your email",
        "E mail id", "email address", "Your Gmail ID",
        "Email address for further communication", "Mail Id", "Enter a valid email ID",
        "Registered email address", "Active email id",
        "Email ID (we will contact you here)", "E-Mail Address", "Your mail",
        "Email of the candidate", "Preferred email address", "Email for correspondence",
        "What is your email address?", "Participant email", "Your email id please",
        "Email address of the applicant",
    ],
    "phone": [
        "Phone", "Phone Number", "Mobile", "Mobile No.", "Mobile Number",
        "Contact Number", "Contact No.", "Your phone number", "Phone no", "Mob. No.",
        "Cell number", "WhatsApp number", "WhatsApp No.", "Enter your mobile number",
        "10-digit mobile number", "Contact number (WhatsApp preferred)",
        "Candidate mobile number", "Student phone number", "Ph. No.",
        "Telephone number", "Primary contact number", "Your contact number",
        "Mobile no. (without country code)", "Phone number with country code",
        "Whatsapp contact number", "Applicant's mobile number", "Active mobile number",
        "Contact details (phone)", "What is your phone number?", "Your mobile",
        "Mobile Number for communication", "Participant contact number",
        "Personal mobile number", "Please enter your 10 digit phone number",
        "Phone (+91)", "Mobile / WhatsApp number", "Contact no. of the candidate",
        "Number to reach you", "Registered mobile number", "Cell phone",
    ],
    "college": [
        "College", "College Name", "Name of the College", "Institute", "Institute Name",
        "University", "University Name", "Name of your college", "Name of the Institution",
        "Institution", "College/University",
        "Name of the institute you are studying in", "Your college name",
        "Which college do you study in?", "College / Institution Name", "Current college",
        "College studying in", "Name of the Institution you are studying in",
        "Educational Institution", "Name of University/College", "Studying at",
        "Your institute", "Enter your college name", "Name of the University",
        "Which university are you from?", "College Name (Full form, no abbreviations)",
        "Institute/University", "Current Institution", "College or University",
        "Name of College/Institute", "Where do you study?", "Your university",
        "Name of your institution", "Parent institution", "Affiliated college",
        "Student's college", "Present college", "Alma mater", "Current university",
    ],
    "degree": [
        "Degree", "Qualification", "Course", "Course pursuing", "Degree pursuing",
        "Highest qualification", "Current qualification", "Programme", "Program",
        "Degree/Course", "Which degree are you pursuing?", "Your degree",
        "Educational qualification", "Course Name", "Name of the course",
        "Degree (B.Tech/B.E/BCA etc.)", "Program of study", "Current course",
        "Pursuing degree", "Academic program", "Course/Degree", "Qualification pursuing",
        "Under graduation course", "UG/PG", "Degree program", "Course enrolled in",
        "What course are you studying?", "Education level", "Degree you are pursuing",
        "Course undertaken", "Course of study", "Present qualification", "Degree name",
        "Degree Level", "Which program are you enrolled in?", "Academic qualification",
        "Qualification (Pursuing)", "Programme of study", "Course doing", "Current degree",
    ],
}

for name, phrases in BANK.items():
    with open(OUT / f"{name}.json", "w", encoding="utf-8") as f:
        json.dump(phrases, f, indent=1, ensure_ascii=False)
    print(name, len(phrases))