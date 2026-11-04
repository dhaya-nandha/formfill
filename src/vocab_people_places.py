from src.schema import INDIAN_STATES

FIRST_NAMES = [
    "Aarav", "Aditya", "Akash", "Amit", "Anil", "Anirudh", "Arjun", "Arnav", "Ashwin", "Bharath",
    "Chaitanya", "Deepak", "Dev", "Dhruv", "Gautam", "Gopal", "Harsha", "Harish", "Hemanth", "Ishaan",
    "Jayanth", "Karthik", "Kiran", "Krishna", "Kunal", "Lakshman", "Manoj", "Mohan", "Naveen", "Nikhil",
    "Nitin", "Pranav", "Prasad", "Pratik", "Rahul", "Rajesh", "Rakesh", "Ram", "Ramesh", "Ravi",
    "Rohan", "Rohit", "Sai", "Sandeep", "Sanjay", "Santhosh", "Sarath", "Satish", "Shiva", "Siddharth",
    "Srikanth", "Suraj", "Suresh", "Tarun", "Uday", "Varun", "Venkat", "Vignesh", "Vijay", "Vikram",
    "Vinay", "Vishal", "Yash", "Yogesh", "Mohammed", "Imran", "Farhan", "Zaid", "Faizan", "Arman",
    "Rizwan", "Tejas", "Mahesh", "Surya", "Dinesh", "Ganesh", "Bhanu", "Charan", "Teja", "Mukesh",
    "Prakash", "Ajay", "Vivek", "Abhishek", "Aniket", "Shubham", "Saurav", "Pavan", "Lokesh", "Manish",
    "Praneeth", "Rishi", "Sathish", "Harshith", "Dheeraj", "Jagadeesh", "Koushik", "Nandan", "Omkar",
    "Parth", "Raghav", "Sachin", "Tushar", "Vamsi", "Mithun", "Naresh", "Pradeep", "Sudheer",
    "Aadhya", "Aishwarya", "Ananya", "Anjali", "Anusha", "Aparna", "Archana", "Bhavana", "Deepika",
    "Divya", "Gayathri", "Harini", "Ishita", "Jahnavi", "Kavya", "Keerthi", "Lakshmi", "Lavanya",
    "Madhavi", "Meghana", "Meera", "Mounika", "Nandini", "Neha", "Nisha", "Pooja", "Prathyusha",
    "Priya", "Priyanka", "Radhika", "Rashmi", "Rekha", "Revathi", "Riya", "Sahithi", "Sanjana",
    "Sathvika", "Shreya", "Shruthi", "Sindhu", "Sneha", "Sowmya", "Swathi", "Tanvi", "Uma",
    "Vaishnavi", "Varsha", "Vidya", "Yamini", "Zoya", "Fatima", "Ayesha", "Sana", "Nikitha",
    "Pallavi", "Manasa", "Harika", "Chandana", "Bindu", "Sirisha", "Tejaswini", "Sravani", "Navya",
    "Deepthi", "Roshni", "Kritika", "Shalini", "Simran", "Suhana", "Isha",
]

SURNAMES = [
    "Reddy", "Naidu", "Rao", "Sharma", "Verma", "Gupta", "Singh", "Kumar", "Patel", "Shah",
    "Mehta", "Joshi", "Iyer", "Iyengar", "Nair", "Menon", "Pillai", "Das", "Dutta", "Bose",
    "Ghosh", "Banerjee", "Chatterjee", "Mukherjee", "Sen", "Roy", "Khan", "Ahmed", "Ali", "Sheikh",
    "Siddiqui", "Qureshi", "Pathan", "Kapoor", "Malhotra", "Chopra", "Bhatia", "Arora", "Agarwal",
    "Jain", "Bansal", "Mishra", "Pandey", "Tiwari", "Dubey", "Shukla", "Yadav", "Chauhan", "Rathore",
    "Thakur", "Desai", "Kulkarni", "Deshpande", "Patil", "Pawar", "Jadhav", "Shinde", "More", "Kale",
    "Gaikwad", "Naik", "Rane", "Shetty", "Hegde", "Bhat", "Kamath", "Prabhu", "Gowda", "Murthy",
    "Chandra", "Raju", "Varma", "Kolla", "Kota", "Gadde", "Chowdary", "Choudhary", "Yerra",
    "Nandyala", "Vemula", "Pothula", "Bandi", "Sunkara", "Mandava", "Tadepalli", "Pasupuleti",
    "Rayudu", "Subramanian", "Krishnan", "Raman", "Venkatesh", "Sundaram", "Balaji", "Natarajan",
    "Ramasamy", "Chandrasekar", "Narayanan", "Swamy", "Sastry", "Sarma", "Prasad", "Babu", "Goud",
    "Yadagiri", "Mohan", "Mahajan", "Saxena", "Srivastava", "Bhardwaj", "Kaur", "Gill", "Sandhu",
    "Dhillon", "Grewal", "Sethi", "Khanna", "Tandon", "Trivedi", "Bhatt", "Vyas", "Parekh", "Modi",
    "Soni", "Rajput", "Dixit", "Awasthi", "Bhattacharya", "Chakraborty", "Sarkar", "Biswas",
    "Mondal", "Mahato", "Barman", "Hazarika", "Borah", "Gogoi",
]

# (full name, short form)
REAL_COLLEGES = [
    ("Indian Institute of Technology Madras", "IIT Madras"),
    ("Indian Institute of Technology Bombay", "IIT Bombay"),
    ("Indian Institute of Technology Delhi", "IIT Delhi"),
    ("Indian Institute of Technology Kanpur", "IIT Kanpur"),
    ("Indian Institute of Technology Kharagpur", "IIT Kharagpur"),
    ("Indian Institute of Technology Hyderabad", "IIT Hyderabad"),
    ("Indian Institute of Technology Roorkee", "IIT Roorkee"),
    ("Indian Institute of Technology Guwahati", "IIT Guwahati"),
    ("National Institute of Technology Tiruchirappalli", "NIT Trichy"),
    ("National Institute of Technology Warangal", "NIT Warangal"),
    ("National Institute of Technology Karnataka, Surathkal", "NITK Surathkal"),
    ("National Institute of Technology Calicut", "NIT Calicut"),
    ("National Institute of Technology Rourkela", "NIT Rourkela"),
    ("National Institute of Technology Andhra Pradesh", "NIT Andhra Pradesh"),
    ("National Institute of Technology Kurukshetra", "NIT Kurukshetra"),
    ("National Institute of Technology Durgapur", "NIT Durgapur"),
    ("National Institute of Technology Silchar", "NIT Silchar"),
    ("Motilal Nehru National Institute of Technology Allahabad", "MNNIT Allahabad"),
    ("Maulana Azad National Institute of Technology Bhopal", "MANIT Bhopal"),
    ("Visvesvaraya National Institute of Technology Nagpur", "VNIT Nagpur"),
    ("Malaviya National Institute of Technology Jaipur", "MNIT Jaipur"),
    ("International Institute of Information Technology Hyderabad", "IIIT Hyderabad"),
    ("International Institute of Information Technology Bangalore", "IIIT Bangalore"),
    ("Indraprastha Institute of Information Technology Delhi", "IIIT Delhi"),
    ("Birla Institute of Technology and Science, Pilani", "BITS Pilani"),
    ("Vellore Institute of Technology", "VIT Vellore"),
    ("VIT-AP University", "VIT-AP"),
    ("VIT Bhopal University", "VIT Bhopal"),
    ("Vellore Institute of Technology, Chennai", "VIT Chennai"),
    ("SRM Institute of Science and Technology", "SRMIST"),
    ("SRM University AP", "SRM AP"),
    ("Amrita Vishwa Vidyapeetham", "Amrita"),
    ("Manipal Institute of Technology", "MIT Manipal"),
    ("PSG College of Technology", "PSG Tech"),
    ("Anna University", "Anna University"),
    ("College of Engineering Pune", "COEP"),
    ("Delhi Technological University", "DTU"),
    ("Netaji Subhas University of Technology", "NSUT"),
    ("Jadavpur University", "JU"),
    ("Kalinga Institute of Industrial Technology", "KIIT"),
    ("Thapar Institute of Engineering and Technology", "Thapar"),
    ("Amity University", "Amity"),
    ("Lovely Professional University", "LPU"),
    ("Chandigarh University", "CU"),
    ("SASTRA Deemed University", "SASTRA"),
    ("Symbiosis Institute of Technology", "SIT Pune"),
    ("Christ University", "Christ"),
    ("Jawaharlal Nehru Technological University Hyderabad", "JNTUH"),
    ("Jawaharlal Nehru Technological University Kakinada", "JNTUK"),
    ("Osmania University", "OU"),
    ("Andhra University", "AU"),
    ("Visvesvaraya Technological University", "VTU"),
    ("R V College of Engineering", "RVCE"),
    ("B M S College of Engineering", "BMSCE"),
    ("M S Ramaiah Institute of Technology", "MSRIT"),
    ("PES University", "PES"),
    ("Nirma University", "Nirma"),
    ("Pune Institute of Computer Technology", "PICT"),
    ("Veermata Jijabai Technological Institute", "VJTI"),
    ("Shiv Nadar University", "SNU"),
    ("Guru Gobind Singh Indraprastha University", "GGSIPU"),
    ("Bennett University", "Bennett"),
    ("Mahindra University", "Mahindra"),
    ("GITAM University", "GITAM"),
    ("Koneru Lakshmaiah Education Foundation", "KLEF"),
    ("Vignan's Foundation for Science, Technology and Research", "Vignan"),
    ("S R K R Engineering College", "SRKR"),
    ("Kongu Engineering College", "KEC"),
    ("Coimbatore Institute of Technology", "CIT"),
    ("Thiagarajar College of Engineering", "TCE"),
    ("Madras Institute of Technology", "MIT Chennai"),
    ("SSN College of Engineering", "SSNCE"),
    ("Sathyabama Institute of Science and Technology", "Sathyabama"),
    ("Vel Tech Rangarajan Dr. Sagunthala R&D Institute of Science and Technology", "Vel Tech"),
    ("Hindustan Institute of Technology and Science", "HITS"),
    ("Saveetha Engineering College", "SEC"),
    ("Indian Institute of Engineering Science and Technology, Shibpur", "IIEST Shibpur"),
]

_COLLEGE_PREFIXES = [
    "Sri Venkateswara", "Sree Vidyanikethan", "Adithya", "Vasavi", "Gokaraju Rangaraju",
    "Chaitanya Bharathi", "Sir M Visvesvaraya", "Lakireddy Bali Reddy", "Prasad V Potluri",
    "Narayana", "Kakatiya", "Gayatri Vidya Parishad", "Swarnandhra", "Vidya Jyothi",
    "Malla Reddy", "CMR", "Sree Dattha", "Anurag", "Mahatma Gandhi", "Sardar Patel",
    "Rajiv Gandhi", "Dr. Ambedkar", "Netaji", "Bharathiar", "Government", "Shri Ram",
    "St. Josephs", "Loyola", "Karunya", "Kumaraguru",
]
_COLLEGE_SUFFIXES = [
    ("Institute of Technology", "IT"), ("College of Engineering", "CE"),
    ("Engineering College", "EC"), ("Institute of Engineering and Technology", "IET"),
    ("University", "U"), ("Institute of Science and Technology", "IST"),
]


def _initials(text):
    return "".join(w[0] for w in text.replace(".", "").split() if w[0].isalpha()).upper()


GENERATED_COLLEGES = [(f"{p} {s}", f"{_initials(p)}{a}")
                      for p in _COLLEGE_PREFIXES for s, a in _COLLEGE_SUFFIXES]

COLLEGES = REAL_COLLEGES + GENERATED_COLLEGES

CITIES = [
    ("Visakhapatnam", "Andhra Pradesh"), ("Vijayawada", "Andhra Pradesh"), ("Guntur", "Andhra Pradesh"),
    ("Amaravati", "Andhra Pradesh"), ("Tirupati", "Andhra Pradesh"), ("Nellore", "Andhra Pradesh"),
    ("Kakinada", "Andhra Pradesh"), ("Rajahmundry", "Andhra Pradesh"), ("Kurnool", "Andhra Pradesh"),
    ("Hyderabad", "Telangana"), ("Warangal", "Telangana"), ("Karimnagar", "Telangana"),
    ("Nizamabad", "Telangana"), ("Secunderabad", "Telangana"),
    ("Chennai", "Tamil Nadu"), ("Coimbatore", "Tamil Nadu"), ("Madurai", "Tamil Nadu"),
    ("Tiruchirappalli", "Tamil Nadu"), ("Salem", "Tamil Nadu"), ("Vellore", "Tamil Nadu"),
    ("Tirunelveli", "Tamil Nadu"), ("Erode", "Tamil Nadu"),
    ("Bengaluru", "Karnataka"), ("Mysuru", "Karnataka"), ("Mangaluru", "Karnataka"),
    ("Hubballi", "Karnataka"), ("Belagavi", "Karnataka"),
    ("Kochi", "Kerala"), ("Thiruvananthapuram", "Kerala"), ("Kozhikode", "Kerala"), ("Thrissur", "Kerala"),
    ("Mumbai", "Maharashtra"), ("Pune", "Maharashtra"), ("Nagpur", "Maharashtra"),
    ("Nashik", "Maharashtra"), ("Aurangabad", "Maharashtra"),
    ("Ahmedabad", "Gujarat"), ("Surat", "Gujarat"), ("Vadodara", "Gujarat"), ("Rajkot", "Gujarat"),
    ("Jaipur", "Rajasthan"), ("Jodhpur", "Rajasthan"), ("Udaipur", "Rajasthan"), ("Kota", "Rajasthan"),
    ("New Delhi", "Delhi"), ("Delhi", "Delhi"),
    ("Lucknow", "Uttar Pradesh"), ("Kanpur", "Uttar Pradesh"), ("Noida", "Uttar Pradesh"),
    ("Varanasi", "Uttar Pradesh"), ("Prayagraj", "Uttar Pradesh"), ("Agra", "Uttar Pradesh"),
    ("Gurugram", "Haryana"), ("Faridabad", "Haryana"),
    ("Ludhiana", "Punjab"), ("Amritsar", "Punjab"), ("Chandigarh", "Chandigarh"),
    ("Kolkata", "West Bengal"), ("Durgapur", "West Bengal"), ("Siliguri", "West Bengal"),
    ("Bhubaneswar", "Odisha"), ("Cuttack", "Odisha"),
    ("Bhopal", "Madhya Pradesh"), ("Indore", "Madhya Pradesh"), ("Patna", "Bihar"),
    ("Ranchi", "Jharkhand"), ("Jamshedpur", "Jharkhand"), ("Raipur", "Chhattisgarh"),
    ("Guwahati", "Assam"), ("Dehradun", "Uttarakhand"), ("Shimla", "Himachal Pradesh"),
    ("Panaji", "Goa"), ("Puducherry", "Puducherry"),
]

if __name__ == "__main__":
    def dups(items):
        seen, d = set(), []
        for x in items:
            if x in seen:
                d.append(x)
            seen.add(x)
        return d

    print("first names :", len(FIRST_NAMES), "| surnames:", len(SURNAMES),
          "| total name words:", len(FIRST_NAMES) + len(SURNAMES), "(need 300+)")
    print("colleges    :", len(COLLEGES), f"(real {len(REAL_COLLEGES)} + generated {len(GENERATED_COLLEGES)}) (need 150+)")
    print("cities      :", len(CITIES), "(need 60+)")
    bad = sorted({s for _, s in CITIES if s not in INDIAN_STATES})
    print("states not in schema:", bad)
    print("duplicate first names:", dups(FIRST_NAMES))
    print("duplicate surnames   :", dups(SURNAMES))
    print("duplicate colleges   :", dups([c[0] for c in COLLEGES]))
    print("duplicate cities     :", dups(CITIES))