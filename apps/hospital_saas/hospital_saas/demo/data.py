"""Static seed data for the client demo (fictional people, Bangladesh context)."""

COMPANY = "CityCare General Hospital"
ABBR = "CCGH"
COUNTRY = "Bangladesh"
CURRENCY = "BDT"
TIMEZONE = "Asia/Dhaka"

# Shared password for the public demo logins (shown on the login page).
DEMO_PASSWORD = "Demo@2026"

# Fictional contact details printed on prescriptions and receipts.
HOSPITAL_CONTACT = {
	"phone_no": "+880 9612-000111",
	"email": "info@citycare.test",
	"website": "citycare.test",
	"address_line1": "House 25, Road 7, Dhanmondi",
	"city": "Dhaka",
	"pincode": "1205",
}

BRANCHES = ["Dhanmondi (Main)", "Uttara"]

EXTRA_DEPARTMENTS = ["General Medicine", "Paediatrics"]

# (first, last, gender, department, branch, OPD fee, IPD visit fee, designation)
DOCTORS = [
	("Farhana", "Rahman", "Female", "Gynaecology", "Dhanmondi (Main)", 1200, 1500, "Consultant"),
	("Mahbubul", "Alam", "Male", "Cardiology", "Dhanmondi (Main)", 1500, 2000, "Professor"),
	("Nusrat", "Jahan", "Female", "Paediatrics", "Dhanmondi (Main)", 1000, 1200, "Consultant"),
	("Kamrul", "Hasan", "Male", "Orthopaedics", "Dhanmondi (Main)", 1200, 1500, "Associate Professor"),
	("Sharmin", "Akter", "Female", "Dermatology", "Uttara", 1000, 1200, "Consultant"),
	("Tanvir", "Ahmed", "Male", "General Medicine", "Uttara", 800, 1000, "Medical Officer"),
	("Rezaul", "Karim", "Male", "Neurology", "Dhanmondi (Main)", 1500, 2000, "Professor"),
	("Ayesha", "Siddiqua", "Female", "ENT", "Uttara", 1000, 1200, "Consultant"),
	("Imran", "Hossain", "Male", "General Surgery", "Dhanmondi (Main)", 1200, 1800, "Consultant"),
	("Sabrina", "Islam", "Female", "Diabetology", "Uttara", 1000, 1200, "Consultant"),
]

MALE_FIRST = [
	"Abdul", "Rafiq", "Shahidul", "Jahangir", "Mizanur", "Habibur", "Anisur", "Sohel", "Rakib",
	"Arif", "Nazmul", "Fahim", "Sajid", "Tariq", "Mamun", "Rashed", "Shafiq", "Zahid", "Babul",
	"Nayeem", "Riyad", "Shakil", "Faruk", "Delwar", "Rubel",
]
FEMALE_FIRST = [
	"Fatema", "Rokeya", "Nasrin", "Shirin", "Taslima", "Moushumi", "Lipi", "Rina", "Sumaiya",
	"Tahmina", "Jannatul", "Sadia", "Mitu", "Shapla", "Rehana", "Parvin", "Nadia", "Farzana",
	"Kulsum", "Laila", "Tania", "Rumana", "Afroza", "Sharmin", "Bilkis",
]
LAST_NAMES = [
	"Hossain", "Rahman", "Islam", "Ahmed", "Khan", "Chowdhury", "Uddin", "Mia", "Sarker", "Talukder",
	"Akter", "Begum", "Bhuiyan", "Molla", "Sheikh", "Haque", "Kabir", "Mahmud", "Roy", "Das",
]
AREAS = [
	"Dhanmondi, Dhaka", "Mirpur, Dhaka", "Uttara, Dhaka", "Mohammadpur, Dhaka", "Gulshan, Dhaka",
	"Banani, Dhaka", "Badda, Dhaka", "Savar, Dhaka", "Gazipur", "Narayanganj", "Tongi, Gazipur",
	"Keraniganj, Dhaka",
]
BLOOD_GROUPS = [
	"A Positive", "B Positive", "O Positive", "AB Positive", "A Negative", "B Negative", "O Negative",
]

# Inpatient layout per branch: (floor, ward, service unit type, room/bed count)
WARDS = {
	"Dhanmondi (Main)": [
		("Level 3", "Male General Ward", "General Ward Bed", 8),
		("Level 3", "Female General Ward", "General Ward Bed", 8),
		("Level 4", "Cabin Block", "Private Cabin", 6),
		("Level 5", "ICU", "ICU Bed", 6),
	],
	"Uttara": [
		("Level 2", "General Ward", "General Ward Bed", 8),
		("Level 3", "Cabin Block", "Private Cabin", 4),
	],
}

# Service unit types: (name, inpatient, allow_appointments, daily rate)
SERVICE_UNIT_TYPES = [
	("General Ward Bed", 1, 0, 1500),
	("Private Cabin", 1, 0, 4500),
	("ICU Bed", 1, 0, 12000),
	("OPD Chamber", 0, 1, 0),
	("Laboratory", 0, 1, 0),
]

DIAGNOSES = [
	"Essential Hypertension", "Type 2 Diabetes Mellitus", "Dengue Fever", "Acute Gastroenteritis",
	"Upper Respiratory Tract Infection", "Typhoid Fever", "Iron Deficiency Anaemia", "Migraine",
	"Lumbar Spondylosis", "Allergic Rhinitis", "Urinary Tract Infection", "Bronchial Asthma",
	"Acid Peptic Disease", "Osteoarthritis Knee", "Contact Dermatitis",
]
ALLERGIES = ["Penicillin", "Sulfa drugs", "Dust", "Seafood", "Peanuts", "Pollen", "NSAIDs", "Latex", "Egg"]

CLINICAL_NOTES = [
	"Advised plenty of fluids and rest. Review after 5 days if symptoms persist.",
	"Low salt, low fat diet advised. Continue regular walking for 30 minutes.",
	"Explained the condition and medicines. Return immediately if fever exceeds 103 F.",
	"Blood sugar log to be maintained. Follow up with reports in 2 weeks.",
	"Avoid oily and spicy food. Take medicines after meals.",
	"Physiotherapy advised. Avoid lifting heavy weights.",
	"Steam inhalation twice daily. Avoid cold drinks.",
	"Check blood pressure at home morning and evening and bring the readings.",
]

NURSE_NOTES = [
	"Patient rested well overnight. IV line patent, no swelling at the site.",
	"Medicines given on time. Patient tolerated oral diet.",
	"Complained of mild pain, informed duty doctor. Analgesic given as advised.",
	"Vitals stable. Encouraged to walk in the ward twice today.",
	"Dressing changed, wound clean and dry.",
	"Intake and output charted. Urine output adequate.",
	"Family counselled about the diet plan and discharge preparation.",
	"Blood sample collected for the morning tests and sent to the lab.",
]

IPD_ADVANCE = {"General Ward Bed": 5000, "Private Cabin": 15000, "ICU Bed": 30000}

COMPLAINTS = [
	"Fever", "Headache", "Cough", "Chest Pain", "Abdominal Pain", "Shortness of Breath",
	"Joint Pain", "Back Pain", "Skin Rash", "Dizziness", "Vomiting", "Fatigue",
]

# Lab tests: (name, department, rate, [(event, uom, normal range, low, high, decimals)])
LAB_TESTS = [
	(
		"Complete Blood Count (CBC)", "Haematology", 600,
		[
			("Haemoglobin", "g/dL", "12.0 - 17.0 g/dL", 9.5, 16.5, 1),
			("Total WBC Count", "/cumm", "4,000 - 11,000 /cumm", 4200, 14500, 0),
			("Platelet Count", "/cumm", "150,000 - 450,000 /cumm", 90000, 380000, 0),
			("ESR", "mm/hr", "0 - 20 mm/hr", 5, 45, 0),
		],
	),
	("Fasting Blood Sugar (FBS)", "Biochemistry", 250, [("Glucose (Fasting)", "mmol/L", "3.9 - 6.1 mmol/L", 4.2, 11.8, 1)]),
	("HbA1c", "Biochemistry", 1200, [("HbA1c", "%", "4.0 - 5.6 %", 5.0, 9.8, 1)]),
	(
		"Lipid Profile", "Biochemistry", 1500,
		[
			("Total Cholesterol", "mg/dL", "< 200 mg/dL", 150, 260, 0),
			("Triglycerides", "mg/dL", "< 150 mg/dL", 90, 280, 0),
			("HDL Cholesterol", "mg/dL", "> 40 mg/dL", 32, 60, 0),
			("LDL Cholesterol", "mg/dL", "< 100 mg/dL", 80, 180, 0),
		],
	),
	("Serum Creatinine", "Biochemistry", 400, [("Creatinine", "mg/dL", "0.6 - 1.2 mg/dL", 0.6, 2.1, 2)]),
	("Dengue NS1 Antigen", "Serology", 500, [("NS1 Antigen", "", "Negative", None, None, 0)]),
	("SGPT (ALT)", "Biochemistry", 400, [("SGPT", "U/L", "7 - 56 U/L", 15, 95, 0)]),
	("Serum TSH", "Biochemistry", 900, [("TSH", "mIU/L", "0.4 - 4.0 mIU/L", 0.5, 7.5, 2)]),
]

# Radiology (descriptive reports): (name, rate, [(particular, sample findings)])
RADIOLOGY_TESTS = [
	("X-Ray Chest PA View", 600, [
		("Findings", "Lung fields are clear. Cardiac size within normal limits. Both costophrenic angles are clear."),
		("Impression", "Normal chest radiograph."),
	]),
	("USG Whole Abdomen", 1500, [
		("Liver", "Normal in size with mildly increased echotexture. No focal lesion."),
		("Gall bladder", "Well distended. No calculus seen."),
		("Kidneys", "Both kidneys normal in size and echotexture. No calculus or hydronephrosis."),
		("Impression", "Grade I fatty liver. Otherwise normal study."),
	]),
	("X-Ray Lumbosacral Spine AP/Lat", 800, [
		("Findings", "Reduced L4-L5 disc space with marginal osteophytes. Alignment maintained."),
		("Impression", "Lumbar spondylosis."),
	]),
	("CT Scan Brain (Plain)", 4500, [
		("Findings", "No intracranial haemorrhage or mass effect. Ventricles normal in size."),
		("Impression", "Normal CT scan of brain."),
	]),
	("Echocardiography", 2500, [
		("Findings", "Normal chamber dimensions. LVEF 60%. No regional wall motion abnormality."),
		("Impression", "Normal echocardiogram."),
	]),
	("X-Ray Knee Joint AP/Lat", 700, [
		("Findings", "Reduced medial joint space with osteophytes."),
		("Impression", "Osteoarthritis of knee joint."),
	]),
]

# Pharmacy items: (code, name, dosage form, rate, opening qty, reorder level)
PHARMACY_ITEMS = [
	("NAPA-500", "Napa 500mg (Paracetamol)", "Tablet", 1.2, 5000, 1000),
	("SECLO-20", "Seclo 20mg (Omeprazole)", "Capsule", 6, 2400, 500),
	("AMLO-5", "Amlodipine 5mg", "Tablet", 5, 1500, 400),
	("METF-500", "Metformin 500mg", "Tablet", 4, 1800, 400),
	("AZITH-500", "Azithromycin 500mg", "Tablet", 40, 300, 150),
	("MONTE-10", "Montelukast 10mg", "Tablet", 15, 120, 200),
	("CEFT-1G", "Ceftriaxone 1g Injection", "Injection", 180, 80, 100),
	("ORS-SALINE", "Oral Saline (ORS) Sachet", "Syrup", 6, 900, 300),
	("NS-500", "Normal Saline 0.9% 500ml", "Injection", 95, 140, 100),
	("INS-RAPID", "Insulin Rapid 10ml Vial", "Injection", 650, 35, 40),
]

SUPPLIERS = ["Square Pharmaceuticals Ltd.", "Beximco Pharmaceuticals Ltd.", "Incepta Pharmaceuticals Ltd."]

# Staff (non-doctor employees): (first, last, gender, designation, department, branch)
STAFF = [
	("Rupa", "Akter", "Female", "Senior Staff Nurse", "Nursing", "Dhanmondi (Main)"),
	("Moni", "Begum", "Female", "Staff Nurse", "Nursing", "Dhanmondi (Main)"),
	("Shilpi", "Rani", "Female", "Staff Nurse", "Nursing", "Dhanmondi (Main)"),
	("Joynal", "Abedin", "Male", "Staff Nurse", "Nursing", "Uttara"),
	("Sumi", "Khatun", "Female", "Staff Nurse", "Nursing", "Uttara"),
	("Rasel", "Mia", "Male", "Front Desk Executive", "Front Office", "Dhanmondi (Main)"),
	("Popy", "Sarker", "Female", "Front Desk Executive", "Front Office", "Uttara"),
	("Hasib", "Uddin", "Male", "Lab Technologist", "Laboratory", "Dhanmondi (Main)"),
	("Liton", "Das", "Male", "Lab Technologist", "Laboratory", "Uttara"),
	("Anwar", "Hossain", "Male", "Pharmacist", "Pharmacy", "Dhanmondi (Main)"),
	("Tanjila", "Ahmed", "Female", "Radiologist", "Radiology", "Dhanmondi (Main)"),
	("Selina", "Parvin", "Female", "Accounts Officer", "Accounts", "Dhanmondi (Main)"),
	("Masud", "Rana", "Male", "Branch Manager", "Administration", "Uttara"),
	("Shafiqul", "Islam", "Male", "Managing Director", "Administration", "Dhanmondi (Main)"),
]

# Demo logins, one per role profile (see hospital_saas/roles.py), shown on the
# login page when the site runs in demo mode.
# (email, first name, last name, role profile, linked doctor index or None)
DEMO_USERS = [
	("superadmin@citycare.test", "Shafiqul", "Islam", "Super Admin", None),
	("admin@citycare.test", "Masud", "Rana", "Admin", None),
	("doctor@citycare.test", "Mahbubul", "Alam", "Doctor", 1),
	("pharmacist@citycare.test", "Anwar", "Hossain", "Pharmacist", None),
	("pathologist@citycare.test", "Hasib", "Uddin", "Pathologist", None),
	("radiologist@citycare.test", "Tanjila", "Ahmed", "Radiologist", None),
	("accountant@citycare.test", "Selina", "Parvin", "Accountant", None),
	("reception@citycare.test", "Rasel", "Mia", "Receptionist", None),
	("nurse@citycare.test", "Rupa", "Akter", "Nurse", None),
	("patient@citycare.test", "", "", "Patient", None),  # name taken from the patient record,
]

# Stage 0 logins replaced by the list above; disabled on existing sites.
LEGACY_DEMO_USERS = ["admin.demo@citycare.test", "lab@citycare.test", "accounts@citycare.test"]

MODES_OF_PAYMENT = ["Cash", "bKash", "Nagad", "Card"]
