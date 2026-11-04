import json
import re
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "phrasebank"


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def dedupe(phrases):
    seen, clean = set(), []
    for ph in phrases:
        n = norm(ph)
        if n and n not in seen:
            seen.add(n)
            clean.append(ph)
    return clean


LINKEDIN_EXTRA = [
    "LinkedIn profile ID", "Paste your LinkedIn profile URL here",
    "Your LinkedIn profile link", "Link your LinkedIn account",
]

OPEN_TEXT = [
    "Why do you want to join us?", "Why are you interested in this role?",
    "Tell us about yourself", "Describe yourself in a few lines",
    "Describe a project you have worked on", "Why should we select you?",
    "What are your strengths and weaknesses?", "What motivates you?",
    "Where do you see yourself in 5 years?", "Tell us about your achievements",
    "Describe your most challenging project", "What are your career goals?",
    "Why do you want this internship?", "What makes you a good fit for this position?",
    "Write a short bio", "Brief introduction about yourself",
    "Explain your experience with machine learning", "What do you expect from this internship?",
    "Describe a time you solved a difficult problem", "Share your learning journey",
    "Statement of purpose", "Cover letter", "Why do you want to be part of our club?",
    "What can you contribute to our team?", "Describe your leadership experience",
    "Tell us about a failure and what you learned", "Any additional comments?",
    "Anything else you would like us to know?", "What are your hobbies and interests?",
    "Explain your idea in brief", "Describe your hackathon project idea",
    "What problem does your solution solve?", "Tell us why you are passionate about technology",
    "Write about your previous internship experience", "Describe your role in your last team project",
    "What do you hope to learn from this program?", "Summarize your work experience",
    "How did you hear about us and why are you applying?", "Describe your technical background in detail",
    "What is your biggest achievement so far?", "Mention any research work or publications",
    "Elaborate on your skills and how you used them", "Write about yourself in 100 words",
    "Why do you think you are the right candidate?", "Describe your dream job",
    "Explain a concept you recently learned", "Suggestions or feedback for us",
    "Do you have any questions for us?", "Short note on your extracurricular activities",
    "Describe your approach to teamwork",
]

UNSUPPORTED = [
    # personal details
    "Date of Birth", "DOB", "Birth date", "Age", "Gender", "Sex", "Marital status",
    "Nationality", "Religion", "Category (General/OBC/SC/ST)", "Caste", "Blood group",
    "Mother tongue", "Languages known", "Languages you speak", "Hometown",
    "Place of birth", "Disability status", "Are you differently abled?",
    # family
    "Father's name", "Mother's name", "Guardian name", "Parent's contact number",
    "Father's occupation", "Mother's occupation", "Parent's email", "Annual family income",
    "Emergency contact name", "Emergency contact number", "Sibling details",
    # address and ids
    "Address", "Permanent address", "Current address", "Residential address",
    "Pincode", "PIN code", "Zip code", "Country", "District", "Village/Town",
    "Landmark", "Aadhaar number", "PAN number", "Passport number", "Voter ID",
    "Driving license number", "College ID number", "Roll number", "Registration number",
    "Enrollment number", "Student ID", "Employee ID", "Hall ticket number",
    # school marks
    "10th percentage", "12th percentage", "10th marks", "12th marks", "SSC percentage",
    "HSC percentage", "Class 10 board", "Class 12 board", "School name",
    "10th passing year", "12th passing year", "Percentage", "Marks obtained",
    "Backlogs", "Number of arrears", "Current semester", "Semester",
    "JEE rank", "Entrance exam score", "GATE score", "Diploma percentage",
    # work and job terms
    "Expected stipend", "Expected salary", "Current CTC", "Expected CTC",
    "Notice period", "Years of experience", "Total work experience",
    "Current company", "Previous employer", "Current designation",
    "Are you currently employed?", "Reason for leaving last job",
    # availability and preferences
    "Availability", "When can you start?", "Preferred start date", "Internship duration",
    "How many hours can you commit per week?", "Are you willing to relocate?",
    "Work mode preference (remote/onsite)", "Preferred work location",
    "Are you available for full-time?", "Preferred time slot", "Shift preference",
    "Are you comfortable with night shifts?", "Can you attend the interview offline?",
    "Preferred interview date", "Preferred interview time",
    # links and files
    "Resume link", "Upload your resume", "Upload your CV", "Portfolio link",
    "Personal website", "Google Drive link", "YouTube channel link", "Twitter handle",
    "Instagram handle", "Kaggle profile", "LeetCode profile", "HackerRank profile",
    "Upload your photo", "Upload ID proof", "Upload marksheet", "Upload certificate",
    "Link to your project demo", "Behance profile",
    # referral and misc
    "Referral name", "Referred by", "How did you hear about us?", "Source of information",
    "Referral code", "Promo code", "Coupon code", "Do you have a laptop?",
    "T-shirt size", "Food preference (veg/non-veg)", "Accommodation required?",
    "Do you have any allergies?", "Do you agree to the terms and conditions?",
    "Declaration", "Signature", "Date", "Place", "Time slot",
    "Team name", "Team size", "Team member names", "Team leader email",
    "Number of participants", "Track selection", "Hackathon problem statement ID",
    "Previous hackathon experience", "Are you a member of our club?",
    "Which events will you attend?", "Workshop preference", "Session you want to join",
    "Transaction ID", "Payment screenshot", "UPI ID", "Bank account number",
    "IFSC code", "Mode of payment", "Registration fee paid",
    "Do you have any certifications?", "Number of projects completed",
    "Number of internships done", "Awards and honors", "Scholarships received",
    "Do you have a driving license?", "Vehicle number", "Mode of transport",
    "Seminar topic", "Course instructor name", "Mentor name", "Supervisor email",
    "Rate your English proficiency", "Rate your communication skills from 1 to 5",
    "Overall feedback rating", "How satisfied are you with the process?",
]

with open(OUT / "linkedin.json", encoding="utf-8") as f:
    linkedin = dedupe(json.load(f) + LINKEDIN_EXTRA)

for name, phrases in [
    ("linkedin", linkedin),
    ("open_text", dedupe(OPEN_TEXT)),
    ("unsupported", dedupe(UNSUPPORTED)),
]:
    with open(OUT / f"{name}.json", "w", encoding="utf-8") as f:
        json.dump(phrases, f, indent=1, ensure_ascii=False)
    print(name, len(phrases))