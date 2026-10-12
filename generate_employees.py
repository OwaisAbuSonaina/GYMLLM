import os
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

# ==========================================
# 1. CONSTANTS & COMPLIANCE RULES
# ==========================================
OUTPUT_DIR = "./knowledge-base/employees"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Levantine Name Pools (English, Arabic)
MALE_FIRST = [("Ahmad", "أحمد"), ("Omar", "عمر"), ("Tareq", "طارق"), ("Yazan", "يزن"), ("Laith", "ليث"), ("Zaid", "زيد"), ("Mahmoud", "محمود"), ("Fadi", "فادي"), ("Rami", "رامي"), ("Karam", "كرم")]
FEMALE_FIRST = [("Haya", "هيا"), ("Farah", "فرح"), ("Noor", "نور"), ("Rania", "رانيا"), ("Zeina", "زينة"), ("Salma", "سلمى"), ("Tala", "تالا"), ("Lana", "لانا"), ("Sara", "سارة"), ("Dina", "دينا")]
LAST_NAMES = [("Almasri", "المصري"), ("Khoury", "خوري"), ("Haddad", "حداد"), ("Majali", "المجالي"), ("Nsour", "النسور"), ("Fakhoury", "فاخوري"), ("Qudah", "القضاة"), ("Khasawneh", "الخصاونة"), ("Rifaat", "رفعت"), ("Hasan", "حسن")]

SALARY_BANDS = {
    "G1": (300, 400), "G2": (380, 520), "G3": (500, 800), "G4": (750, 1100),
    "G5": (1000, 1550), "G6": (1500, 2400), "G7": (2300, 3600), "G8": (3500, 6500)
}

CURRENT_DATE = datetime(2026, 10, 12)

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================
def generate_name():
    is_male = random.choice([True, False])
    first = random.choice(MALE_FIRST) if is_male else random.choice(FEMALE_FIRST)
    middle = random.choice(MALE_FIRST)
    third = random.choice(MALE_FIRST)
    last = random.choice(LAST_NAMES)
    
    en_name = f"{first[0]} {middle[0]} {third[0]} {last[0]}"
    ar_name = f"{first[1]} {middle[1]} {third[1]} {last[1]}"
    email = f"{first[0].lower()}.{last[0].lower()}@theyardjo.com"
    return en_name, ar_name, email

def generate_id_and_mobile():
    # 85% Jordanian, 15% Expat
    if random.random() < 0.85:
        nat_id = str(random.choice([99, 98])) + "".join([str(random.randint(0, 9)) for _ in range(8)])
        nationality = "Jordanian"
    else:
        nat_id = random.choice(["A", "B", "P"]) + "".join([str(random.randint(0, 9)) for _ in range(7)])
        nationality = random.choice(["Egyptian", "Syrian", "Lebanese"])
    
    mobile = f"+962 7 {random.choice([7, 8, 9])}{random.randint(100,999)} {random.randint(1000,9999)}"
    return nat_id, nationality, mobile

def calculate_dates(est_year):
    start_date = datetime(est_year, 1, 1)
    hire_date = fake.date_between_dates(date_start=start_date, date_end=CURRENT_DATE - timedelta(days=90))
    tenure_years = round((CURRENT_DATE.date() - hire_date).days / 365.25, 1)
    leave_entitlement = 21 if tenure_years >= 5 else 14
    remaining = round(random.uniform(0, leave_entitlement), 1)
    return hire_date.strftime("%Y-%m-%d"), tenure_years, leave_entitlement, remaining

def get_salary_and_ssc(grade):
    base = round(random.uniform(*SALARY_BANDS[grade]), 2)
    emp_ssc = round(base * 0.075, 2)
    employer_ssc = round(base * 0.1425, 2)
    net = round(base - emp_ssc, 2)
    ot_eligible = grade in ["G1", "G2", "G3", "G4"]
    return base, emp_ssc, employer_ssc, net, ot_eligible

def format_markdown(emp):
    # Determine fitness specific fields
    is_fitness = emp['department'] == 'Fitness Operations' or 'Trainer' in emp['job_title'] or 'Instructor' in emp['job_title']
    
    md_content = f"""---
employee_id: "{emp['emp_id']}"
full_name_en: "{emp['full_name_en']}"
full_name_ar: "{emp['full_name_ar']}"
email: "{emp['email']}"
mobile: "{emp['mobile']}"
national_id_or_permit: "{emp['national_id']}"
nationality: "{emp['nationality']}"
branch_id: "{emp['branch_id']}"
department: "{emp['department']}"
job_title: "{emp['job_title']}"
grade: "{emp['grade']}"
reports_to_id: "{emp['reports_to_id']}"
hire_date: "{emp['hire_date']}"
contract_type: "{random.choice(['Limited', 'Unlimited'])}"
employment_status: "Active"
shift_code: "{emp['shift_code']}"
compensation:
  base_salary_jod: {emp['base']}
  social_security_deduction_jod: {emp['emp_ssc']}
  employer_social_security_jod: {emp['employer_ssc']}
  net_payable_base_jod: {emp['net']}
  overtime_eligible: {str(emp['ot_eligible']).lower()}
compliance:
  tenure_years: {emp['tenure']}
  annual_leave_entitlement_days: {emp['leave_entitlement']}
  remaining_leave_balance: {emp['remaining_leave']}
  reps_jordan_certified: {str(is_fitness).lower()}
  reps_jordan_id: "{'REPS-JO-' + str(random.randint(1000, 9999)) if is_fitness else 'null'}"
  cpr_aed_expiry: "{(CURRENT_DATE + timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d') if is_fitness else 'null'}"
  security_clearance_valid_until: "{(CURRENT_DATE + timedelta(days=random.randint(90, 730))).strftime('%Y-%m-%d')}"
---

# Employee Profile: {emp['full_name_en']} ({emp['emp_id']})

## 1. Professional Overview & Role Description
{emp['full_name_en']} serves as a {emp['job_title']} within the {emp['department']} department at {emp['branch_id']}. 
Key responsibilities include maintaining operational excellence, adhering to gym safety protocols, and supporting member success. 

## 2. Reporting & Organizational Lines
- **Direct Supervisor:** Manager ID {emp['reports_to_id']}
- **Subordinates:** {'Various departmental staff' if emp['grade'] in ['G4', 'G5', 'G6', 'G7', 'G8'] else 'None'}

## 3. Accreditations, Licensing & Compliance Register
- Good Conduct Certificate: Verified
- Medical Clearance: Passed
- Professional IDs: {'Active REPs Registration' if is_fitness else 'N/A'}

## 4. Performance, Leave Tracking & Disciplinary Records
- Leave balance remains strictly monitored via HQ.
- Disciplinary actions (Article 48): None recorded in the current fiscal year.
"""
    return md_content

# ==========================================
# 3. BUILD ROSTER & HIERARCHY
# ==========================================
def build_roster():
    employees = []
    id_counter = 1
    
    # Track managers for reporting lines
    execs = {}
    branch_managers = {}

    def add_emp(branch_id, est_year, dept, title, grade, shift, specific_name=None, reports_to="TY-EMP-0001"):
        nonlocal id_counter
        emp_id = f"TY-EMP-{id_counter:04d}"
        id_counter += 1
        
        if specific_name:
            en_name, ar_name = specific_name
            email = f"{en_name.split()[0].lower()}.{en_name.split()[-1].lower()}@theyardjo.com"
        else:
            en_name, ar_name, email = generate_name()
            
        nat_id, nat, mobile = generate_id_and_mobile()
        h_date, tenure, l_ent, l_rem = calculate_dates(est_year)
        base, e_ssc, er_ssc, net, ot = get_salary_and_ssc(grade)
        
        emp = {
            "emp_id": emp_id, "full_name_en": en_name, "full_name_ar": ar_name, "email": email, "mobile": mobile,
            "national_id": nat_id, "nationality": nat, "branch_id": branch_id, "department": dept, "job_title": title,
            "grade": grade, "reports_to_id": reports_to, "hire_date": h_date, "shift_code": shift,
            "base": base, "emp_ssc": e_ssc, "employer_ssc": er_ssc, "net": net, "ot_eligible": ot,
            "tenure": tenure, "leave_entitlement": l_ent, "remaining_leave": l_rem
        }
        employees.append(emp)
        return emp_id

    # 1. Predefined Execs (G7-G8)
    ceo_id = add_emp("HQ-ABDN", 2010, "Executive Suite", "Chief Executive Officer (CEO)", "G8", "SH-CORP", specific_name=("Tariq Abdulhadi", "طارق عبدالهادي"), reports_to="Board of Directors")
    execs['COO'] = add_emp("HQ-ABDN", 2010, "Executive Suite", "Chief Operating Officer (COO)", "G8", "SH-CORP", specific_name=("Samir Khoury", "سمير خوري"), reports_to=ceo_id)
    execs['CFO'] = add_emp("HQ-ABDN", 2010, "Executive Suite", "Chief Financial Officer (CFO)", "G8", "SH-CORP", specific_name=("Lina Masri", "لينا المصري"), reports_to=ceo_id)
    execs['Head_Fitness'] = add_emp("HQ-ABDN", 2010, "Directorate", "Head of Fitness", "G7", "SH-CORP", specific_name=("Omar Fakhoury", "عمر فاخوري"), reports_to=execs['COO'])
    execs['Head_Brand'] = add_emp("HQ-ABDN", 2010, "Directorate", "Brand & Member Experience Director", "G7", "SH-CORP", specific_name=("Farah Haddad", "فرح حداد"), reports_to=ceo_id)
    execs['Head_People'] = add_emp("HQ-ABDN", 2010, "Directorate", "Head of People", "G7", "SH-CORP", reports_to=execs['COO'])
    execs['Reg_Ops'] = add_emp("HQ-ABDN", 2010, "Directorate", "Regional Operations Director", "G7", "SH-CORP", reports_to=execs['COO'])

    # 2. Remaining HQ Staff
    hq_roles = [
        ("Human Resources", "HR Manager", "G6", 1, execs['Head_People']),
        ("Human Resources", "HR Specialist", "G5", 2, "HR Manager"), # Will link later
        ("Human Resources", "Payroll & Talent Officer", "G4", 2, "HR Manager"),
        ("Finance & Accounting", "Finance Manager", "G6", 1, execs['CFO']),
        ("Finance & Accounting", "Senior Accountant", "G5", 1, "Finance Manager"),
        ("Finance & Accounting", "Accountant", "G4", 2, "Finance Manager"),
        ("Finance & Accounting", "Procurement/Audit", "G4", 2, "Finance Manager"),
        ("Marketing & Growth", "Marketing Manager", "G6", 1, execs['Head_Brand']),
        ("Marketing & Growth", "Digital Lead", "G5", 1, "Marketing Manager"),
        ("Marketing & Growth", "Graphic Designer", "G4", 1, "Marketing Manager"),
        ("Marketing & Growth", "Content Specialist", "G4", 1, "Marketing Manager"),
        ("IT Systems", "IT Infrastructure Lead", "G6", 1, execs['COO']),
        ("IT Systems", "System Administrator", "G5", 1, "IT Infrastructure Lead"),
        ("IT Systems", "IT Support Specialist", "G4", 2, "IT Infrastructure Lead"),
        ("IT Systems", "Central Facility Engineer", "G4", 2, "IT Infrastructure Lead"),
        ("Logistics", "Admin Assistant", "G2", 1, execs['Reg_Ops']),
        ("Logistics", "Office Driver (HQ)", "G2", 1, execs['Reg_Ops']),
        ("Logistics", "Office Attendant", "G1", 2, execs['Reg_Ops']),
    ]
    
    hq_manager_ids = {}
    for dept, title, grade, count, rep_to in hq_roles:
        for _ in range(count):
            actual_rep = hq_manager_ids.get(rep_to, rep_to) if isinstance(rep_to, str) else rep_to
            emp_id = add_emp("HQ-ABDN", 2010, dept, title, grade, "SH-CORP", reports_to=actual_rep)
            if "Manager" in title or "Lead" in title:
                hq_manager_ids[title] = emp_id

    # 3. Branch Operations Generator
    branches = [
        {"id": "BR-AMN-01", "est": 2010, "roles": {"BM":1, "ABM":1, "Sup":2, "PT":8, "GFI":4, "FDR":6, "Nutr":2, "Facil":6}},
        {"id": "BR-AMN-02", "est": 2014, "roles": {"BM":1, "ABM":1, "Sup":2, "PT":7, "GFI":3, "FDR":5, "Nutr":1, "Facil":7}},
        {"id": "BR-AMN-03", "est": 2017, "roles": {"BM":1, "ABM":1, "Sup":2, "PT":7, "GFI":3, "FDR":5, "Nutr":1, "Facil":5}},
        {"id": "BR-AMN-04", "est": 2019, "roles": {"BM":1, "ABM":1, "Sup":1, "PT":6, "GFI":2, "FDR":4, "Nutr":1, "Facil":5}},
        {"id": "BR-ZRQ-01", "est": 2016, "roles": {"BM":1, "ABM":1, "Sup":2, "PT":6, "GFI":2, "FDR":4, "Nutr":1, "Facil":5}},
        {"id": "BR-IRB-01", "est": 2018, "roles": {"BM":1, "ABM":1, "Sup":2, "PT":7, "GFI":2, "FDR":5, "Nutr":1, "Facil":4}},
        {"id": "BR-AQB-01", "est": 2021, "roles": {"BM":1, "ABM":1, "Sup":1, "PT":6, "GFI":2, "FDR":4, "Nutr":1, "Facil":5}},
    ]

    shifts = ["SH-MOR", "SH-MID", "SH-EVE"]
    
    for b in branches:
        bid = b["id"]
        est = b["est"]
        roles = b["roles"]
        
        bm_id = add_emp(bid, est, "Branch Management", "Branch General Manager (BM)", "G6", "SH-MOR", reports_to=execs['Reg_Ops'])
        
        for _ in range(roles.get("ABM", 0)):
            add_emp(bid, est, "Branch Management", "Assistant Branch Manager", "G5", "SH-MID", reports_to=bm_id)
            
        for _ in range(roles.get("Sup", 0)):
            add_emp(bid, est, "Supervisory", random.choice(["Head Receptionist", "Senior Trainer", "Lead Maintenance Tech"]), "G4", random.choice(shifts), reports_to=bm_id)
            
        for _ in range(roles.get("PT", 0)):
            add_emp(bid, est, "Fitness Operations", "Certified Personal Trainer (PT)", "G3", random.choice(shifts), reports_to=bm_id)
            
        for _ in range(roles.get("GFI", 0)):
            add_emp(bid, est, "Fitness Operations", "Group Fitness Instructor", "G3", random.choice(shifts), reports_to=bm_id)
            
        for _ in range(roles.get("FDR", 0)):
            add_emp(bid, est, "Front of House", "Front Desk Receptionist", "G2", random.choice(shifts), reports_to=bm_id)
            
        for _ in range(roles.get("Nutr", 0)):
            add_emp(bid, est, "Supervisory", "Clinical Nutritionist", "G4", "SH-MOR", reports_to=bm_id)
            
        for _ in range(roles.get("Facil", 0)):
            add_emp(bid, est, "Facility & Maintenance", random.choice(["Cleaner", "Locker Room Attendant"]), "G1", random.choice(shifts), reports_to=bm_id)

    return employees

# ==========================================
# 4. EXECUTE & EXPORT
# ==========================================
if __name__ == "__main__":
    roster = build_roster()
    
    print(f"Total employees generated: {len(roster)}")
    
    for emp in roster:
        # File Naming: TY-EMP-XXXX-first-last.md
        name_parts = emp['full_name_en'].lower().split()
        filename = f"{emp['emp_id']}-{name_parts[0]}-{name_parts[-1]}.md"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(format_markdown(emp))
            
    print(f"Data successfully generated and saved to ./{OUTPUT_DIR}/")