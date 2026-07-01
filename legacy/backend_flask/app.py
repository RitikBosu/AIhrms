import os
import sys
import json
import time
import base64
import threading
import hashlib
import jwt
import requests
import re
from datetime import datetime, timezone
from flask import Flask, request, jsonify, send_from_directory, abort
from PyPDF2 import PdfReader
from dotenv import load_dotenv

# Load env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), '..', 'frontend'), static_url_path='/')

PORT = int(os.environ.get("PORT", 3000))
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "db.json")
TOKEN_SECRET = os.environ.get("TOKEN_SECRET", "fwc-demo-secret-change-before-production")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

ROLE_ACCESS = {
    "admin": ["admin", "hr", "manager", "employee"],
    "hr": ["admin", "hr"],
    "manager": ["admin", "manager"],
    "employee": ["admin", "hr", "manager", "employee"]
}

global_db = None
is_flushing = False
needs_flush = False
db_lock = threading.Lock()

def read_db():
    global global_db
    if global_db is None:
        try:
            if os.path.exists(DB_PATH):
                with open(DB_PATH, 'r', encoding='utf-8') as f:
                    global_db = json.load(f)
            else:
                global_db = {"users": [], "employees": [], "attendance": [], "leaves": [], "candidates": [], "performance": [], "announcements": [], "jobDescription": ""}
        except Exception:
            global_db = {"users": [], "employees": [], "attendance": [], "leaves": [], "candidates": [], "performance": [], "announcements": [], "jobDescription": ""}
    return global_db

def flush_db_thread():
    global is_flushing, needs_flush
    with db_lock:
        if is_flushing or not needs_flush:
            return
        is_flushing = True
        needs_flush = False
    try:
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(global_db, f, indent=2)
    except Exception as e:
        print("Async DB write error:", e)
    finally:
        with db_lock:
            is_flushing = False
            if needs_flush:
                threading.Timer(0.05, flush_db_thread).start()

def write_db(db):
    global global_db, needs_flush
    global_db = db
    needs_flush = True
    if not is_flushing:
        flush_db_thread()

def create_id(prefix):
    return f"{prefix}-{int(time.time()*1000)}-{os.urandom(3).hex()}"

def hash_password(password, salt=None):
    if not salt:
        salt = os.urandom(16).hex()
    hash_val = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1, maxmem=0, dklen=64).hex()
    return f"{salt}:{hash_val}"

def verify_password(password, stored_hash):
    try:
        salt, original_hash = stored_hash.split(":")
        new_hash = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1, maxmem=0, dklen=64).hex()
        return original_hash == new_hash
    except Exception:
        return False

def sign_token(user):
    payload = {
        "id": user["id"],
        "role": user["role"],
        "name": user["name"],
        "exp": int(time.time()) + 60 * 60 * 6
    }
    return jwt.encode(payload, TOKEN_SECRET, algorithm="HS256")

def verify_token(token):
    if not token:
        return None
    try:
        return jwt.decode(token, TOKEN_SECRET, algorithms=["HS256"])
    except Exception:
        return None

def get_user_from_request():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")
    return verify_token(token)

def require_auth(allowed_roles=None):
    if allowed_roles is None:
        allowed_roles = []
    user = get_user_from_request()
    if not user:
        return None, jsonify({"error": "Please login again."}), 401
    if allowed_roles and user["role"] not in allowed_roles:
        return None, jsonify({"error": "You do not have permission for this action."}), 403
    return user, None, None

def public_user(user):
    return {k: v for k, v in user.items() if k != "passwordHash"}

def get_employee_for_user(db, user_id):
    for emp in db.get("employees", []):
        if emp.get("userId") == user_id:
            return emp
    return None

# --- Dashboard ---

def calculate_dashboard(db, user):
    employee = get_employee_for_user(db, user["id"])
    
    attendance_rows = db.get("attendance", [])
    if user["role"] == "employee" and employee:
        attendance_rows = [r for r in attendance_rows if r.get("employeeId") == employee["id"]]
        
    leave_rows = db.get("leaves", [])
    if user["role"] == "employee" and employee:
        leave_rows = [r for r in leave_rows if r.get("employeeId") == employee["id"]]

    employee_count = 1 if user["role"] == "employee" else len(db.get("employees", []))
    candidate_count = len(db.get("candidates", []))
    pending_leaves = len([l for l in leave_rows if l.get("status") == "Pending"])
    present_today = len([r for r in attendance_rows if r.get("status") == "Present"])

    result = {
        "employeeCount": employee_count,
        "candidateCount": candidate_count,
        "pendingLeaves": pending_leaves,
        "presentToday": present_today,
        "attendanceRows": attendance_rows,
        "leaveRows": leave_rows
    }

    my_attendance = [r for r in db.get("attendance", []) if r.get("employeeId") == employee["id"]] if employee else []
    my_leaves = [r for r in db.get("leaves", []) if r.get("employeeId") == employee["id"]] if employee else []
    my_present = len([a for a in my_attendance if a.get("status") == "Present"])
    my_attendance_rate = round((my_present / len(my_attendance)) * 100) if len(my_attendance) > 0 else 100

    result["myActivity"] = {
        "myAttendanceRate": my_attendance_rate,
        "myLeaveBalance": {
            "total": 18,
            "used": len([l for l in my_leaves if l.get("status") == "Approved"]),
            "pending": len([l for l in my_leaves if l.get("status") == "Pending"])
        },
        "recentActions": []
    }

    if user["role"] == "admin":
        risk_levels = ["high" if p.get("rating", 5) < 3 else "medium" if p.get("rating", 5) < 4 else "low" for p in db.get("performance", [])]
        overall_attendance_rate = 100
        total_attendance = len(db.get("attendance", []))
        if total_attendance > 0:
            overall_attendance_rate = round((len([a for a in db.get("attendance", []) if a.get("status") == "Present"]) / total_attendance) * 100)
            
        result["companyOverview"] = {
            "totalEmployees": len(db.get("employees", [])),
            "overallAttendanceRate": overall_attendance_rate,
            "totalOpenPositions": 3,
            "recentHires": 2,
            "attritionRiskSummary": {
                "low": len([r for r in risk_levels if r == "low"]),
                "medium": len([r for r in risk_levels if r == "medium"]),
                "high": len([r for r in risk_levels if r == "high"])
            }
        }

    if user["role"] == "hr":
        result["screeningStats"] = {
            "shortlisted": len([c for c in db.get("candidates", []) if c.get("aiDecision") == "Shortlisted"]),
            "underReview": len([c for c in db.get("candidates", []) if c.get("aiDecision") == "Under Review"]),
            "rejected": len([c for c in db.get("candidates", []) if c.get("aiDecision") == "Rejected"]),
        }

    return result

# --- Groq Integration ---

def call_groq(system_prompt, user_prompt):
    if not GROQ_API_KEY:
        raise Exception("No Groq API Key set")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 1024
    }
    response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
    if response.status_code != 200:
        err_msg = "Groq API error"
        try:
            err_msg = response.json().get("error", {}).get("message", err_msg)
        except Exception:
            pass
        raise Exception(err_msg)
    return response.json()["choices"][0]["message"]["content"].strip()

def extract_json(text):
    raw = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if match:
        raw = match.group(1).strip()
    start_obj = raw.find("{")
    end_obj = raw.rfind("}")
    start_arr = raw.find("[")
    end_arr = raw.rfind("]")
    
    json_string = raw
    if start_obj != -1 and end_obj != -1 and (start_arr == -1 or start_obj < start_arr):
        json_string = raw[start_obj:end_obj+1]
    elif start_arr != -1 and end_arr != -1:
        json_string = raw[start_arr:end_arr+1]
        
    return json.loads(json_string)

def score_resume_fallback(jd_text, resume_text):
    required_skills = ["react", "node", "javascript", "python", "mongodb", "mysql", "postgresql", "ai", "machine learning", "api", "authentication", "git", "cloud"]
    text = str(resume_text).lower()
    matched = [s for s in required_skills if s in text]
    missing = [s for s in required_skills if s not in text][:5]
    score = min(95, 35 + len(matched) * 5)
    decision = "Rejected"
    if score >= 80: decision = "Shortlisted"
    elif score >= 60: decision = "Under Review"
    return {
        "score": score,
        "decision": decision,
        "justification": f"Fallback evaluation. Matched: {', '.join(matched)}.",
        "matchedSkills": matched,
        "gaps": missing,
        "interviewQuestions": ["Tell me about your experience with these skills."]
    }

def create_interview_questions_fallback(skills):
    clean_skills = [s.strip() for s in str(skills).split(",")]
    clean_skills = [s for s in clean_skills if s][:6]
    base_skills = clean_skills if clean_skills else ["JavaScript", "backend APIs", "database design"]
    questions = []
    for skill in base_skills:
        questions.append(f"Explain one project where you used {skill}.")
        questions.append(f"What problem can happen while using {skill}, and how would you solve it?")
    return questions

def create_performance_summary_fallback(emp_name, rating, feedback):
    level = "strong" if rating >= 4 else "steady" if rating >= 3 else "developing"
    return f"{emp_name} has shown {level} performance. The main feedback is: {feedback}. Recommended next step: set one clear improvement goal for the next review cycle."

def predict_attrition_fallback(employee, attendance_rate, leave_count, avg_rating, tenure):
    risk_score = 0
    factors = []
    if attendance_rate < 70:
        risk_score += 35; factors.append(f"Low attendance rate ({attendance_rate}%)")
    elif attendance_rate < 85:
        risk_score += 15; factors.append(f"Below-average attendance ({attendance_rate}%)")
    if avg_rating <= 2:
        risk_score += 30; factors.append(f"Low performance rating ({avg_rating}/5)")
    elif avg_rating <= 3:
        risk_score += 10; factors.append(f"Average performance rating ({avg_rating}/5)")
    if leave_count >= 5:
        risk_score += 15; factors.append(f"High leave frequency ({leave_count} requests)")
    if tenure < 90:
        risk_score += 15; factors.append(f"Short tenure ({tenure} days)")
    if employee.get("salary", 0) < 40000:
        risk_score += 10; factors.append(f"Below-market salary (Rs. {employee.get('salary', 0)})")
    
    risk_level = "High" if risk_score >= 50 else "Medium" if risk_score >= 25 else "Low"
    confidence = min(95, 60 + len(factors) * 7)
    actions = {
        "High": "Schedule a 1-on-1 retention conversation and explore role enrichment or compensation adjustment.",
        "Medium": "Conduct a stay interview to identify motivational drivers and address concerns early.",
        "Low": "Continue current engagement; consider recognising contributions in the next team meeting."
    }
    return {
        "riskLevel": risk_level,
        "factors": factors[:3],
        "retentionAction": actions[risk_level],
        "confidence": confidence
    }

def answer_hr_question_fallback(db, user, question):
    text = question.lower()
    employee = get_employee_for_user(db, user["id"])
    if "leave" in text:
        leave_count = len([l for l in db.get("leaves", []) if l.get("employeeId") == employee["id"]]) if employee else len(db.get("leaves", []))
        return f"The leave policy gives 18 annual leaves. I found {leave_count} leave request(s) connected to your view."
    if "attendance" in text or "present" in text:
        rows = [r for r in db.get("attendance", []) if r.get("employeeId") == employee["id"]] if employee else db.get("attendance", [])
        present = len([r for r in rows if r.get("status") == "Present"])
        return f"Attendance is marked once per working day. Your current view has {present} present record(s)."
    if "salary" in text or "payroll" in text:
        salary = employee.get("salary") if employee else "employee basic salary"
        return f"Payroll uses basic salary, allowances, deductions, and attendance. Current basic salary value: {salary}."
    return "I can help with leave, attendance, payroll, employee data, candidate screening, and HR policies."

# --- API Routes ---

@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    db = read_db()
    body = request.json or {}
    email = str(body.get("email", "")).lower()
    user = next((u for u in db.get("users", []) if u.get("email", "").lower() == email), None)
    if not user or not verify_password(str(body.get("password", "")), user.get("passwordHash", "")):
        return jsonify({"error": "Invalid email or password."}), 401
    return jsonify({"token": sign_token(user), "user": public_user(user)}), 200

@app.route("/api/me", methods=["GET"])
def get_me():
    user, err_res, status = require_auth()
    if err_res: return err_res, status
    db = read_db()
    db_user = next((u for u in db.get("users", []) if u["id"] == user["id"]), None)
    return jsonify({"user": public_user(db_user)}), 200

@app.route("/api/dashboard", methods=["GET"])
def get_dashboard():
    user, err_res, status = require_auth()
    if err_res: return err_res, status
    return jsonify(calculate_dashboard(read_db(), user)), 200

@app.route("/api/employees", methods=["GET"])
def get_employees():
    user, err_res, status = require_auth()
    if err_res: return err_res, status
    db = read_db()
    if user["role"] == "employee":
        emp = get_employee_for_user(db, user["id"])
        return jsonify([emp] if emp else []), 200
    return jsonify(db.get("employees", [])), 200

@app.route("/api/employees", methods=["POST"])
def create_employee():
    user, err_res, status = require_auth(ROLE_ACCESS["hr"])
    if err_res: return err_res, status
    db = read_db()
    body = request.json or {}
    emp = {
        "id": create_id("emp"),
        "userId": "",
        "name": body.get("name"),
        "email": body.get("email"),
        "department": body.get("department"),
        "designation": body.get("designation"),
        "salary": float(body.get("salary", 0)),
        "joiningDate": body.get("joiningDate")
    }
    db.setdefault("employees", []).append(emp)
    write_db(db)
    return jsonify(emp), 201

@app.route("/api/employees/<id>", methods=["PUT", "DELETE"])
def manage_employee(id):
    db = read_db()
    if request.method == "PUT":
        user, err_res, status = require_auth(ROLE_ACCESS["hr"])
        if err_res: return err_res, status
        body = request.json or {}
        emp = next((e for e in db.get("employees", []) if e["id"] == id), None)
        if not emp: return jsonify({"error": "Employee not found."}), 404
        emp.update({
            "name": body.get("name"),
            "email": body.get("email"),
            "department": body.get("department"),
            "designation": body.get("designation"),
            "salary": float(body.get("salary", 0)),
            "joiningDate": body.get("joiningDate")
        })
        write_db(db)
        return jsonify(emp), 200
    else:
        user, err_res, status = require_auth(["admin"])
        if err_res: return err_res, status
        db["employees"] = [e for e in db.get("employees", []) if e["id"] != id]
        write_db(db)
        return jsonify({"ok": True}), 200

@app.route("/api/attendance", methods=["GET"])
def get_attendance():
    user, err_res, status = require_auth()
    if err_res: return err_res, status
    db = read_db()
    if user["role"] == "employee":
        emp = get_employee_for_user(db, user["id"])
        rows = [r for r in db.get("attendance", []) if r.get("employeeId") == emp["id"]] if emp else []
        return jsonify(rows), 200
    return jsonify(db.get("attendance", [])), 200

@app.route("/api/attendance", methods=["POST"])
def mark_attendance():
    user, err_res, status = require_auth()
    if err_res: return err_res, status
    db = read_db()
    body = request.json or {}
    today = datetime.now().strftime("%Y-%m-%d")
    if body.get("date", "") > today:
        return jsonify({"error": "Cannot mark attendance for a future date."}), 400
    emp = get_employee_for_user(db, user["id"]) if user["role"] == "employee" else None
    att = {
        "id": create_id("att"),
        "employeeId": emp["id"] if emp else body.get("employeeId"),
        "date": body.get("date"),
        "status": body.get("status")
    }
    db.setdefault("attendance", []).append(att)
    write_db(db)
    return jsonify(att), 201

@app.route("/api/attendance/bulk", methods=["POST"])
def bulk_attendance():
    user, err_res, status = require_auth(ROLE_ACCESS["hr"])
    if err_res: return err_res, status
    db = read_db()
    body = request.json or {}
    records = body.get("records") or body if isinstance(body, list) else []
    if not isinstance(records, list):
        return jsonify({"error": "Expected an array of attendance records."}), 400
    
    inserted, skipped, errors = 0, 0, []
    for i, rec in enumerate(records):
        if not rec.get("employeeId") or not rec.get("date") or not rec.get("status"):
            errors.append({"row": i+1, "reason": "Missing required fields (employeeId, date, status)"})
            continue
        emp = next((e for e in db.get("employees", []) if e["id"] == rec["employeeId"]), None)
        if not emp:
            errors.append({"row": i+1, "reason": f"Employee {rec['employeeId']} not found"})
            continue
        if rec["status"] not in ["Present", "Absent"]:
            errors.append({"row": i+1, "reason": f"Invalid status: {rec['status']}. Must be Present or Absent"})
            continue
        duplicate = next((a for a in db.get("attendance", []) if a["employeeId"] == rec["employeeId"] and a["date"] == rec["date"]), None)
        if duplicate:
            skipped += 1
            continue
        db.setdefault("attendance", []).append({
            "id": create_id("att"),
            "employeeId": rec["employeeId"],
            "date": rec["date"],
            "status": rec["status"]
        })
        inserted += 1
    write_db(db)
    return jsonify({"inserted": inserted, "skipped": skipped, "errors": errors}), 200

@app.route("/api/leaves", methods=["GET"])
def get_leaves():
    user, err_res, status = require_auth()
    if err_res: return err_res, status
    db = read_db()
    if user["role"] == "employee":
        emp = get_employee_for_user(db, user["id"])
        rows = [r for r in db.get("leaves", []) if r.get("employeeId") == emp["id"]] if emp else []
        return jsonify(rows), 200
    return jsonify(db.get("leaves", [])), 200

@app.route("/api/leaves", methods=["POST"])
def request_leave():
    user, err_res, status = require_auth()
    if err_res: return err_res, status
    db = read_db()
    body = request.json or {}
    emp = get_employee_for_user(db, user["id"]) if user["role"] == "employee" else None
    leave = {
        "id": create_id("leave"),
        "employeeId": emp["id"] if emp else body.get("employeeId"),
        "fromDate": body.get("fromDate"),
        "toDate": body.get("toDate"),
        "reason": body.get("reason"),
        "status": "Pending"
    }
    db.setdefault("leaves", []).append(leave)
    write_db(db)
    return jsonify(leave), 201

@app.route("/api/leaves/<id>", methods=["PATCH"])
def update_leave(id):
    user, err_res, status = require_auth(ROLE_ACCESS["manager"])
    if err_res: return err_res, status
    db = read_db()
    body = request.json or {}
    leave = next((l for l in db.get("leaves", []) if l["id"] == id), None)
    if not leave: return jsonify({"error": "Leave not found."}), 404
    leave["status"] = body.get("status")
    write_db(db)
    return jsonify(leave), 200

@app.route("/api/payroll", methods=["GET"])
def get_payroll():
    user, err_res, status = require_auth()
    if err_res: return err_res, status
    db = read_db()
    def payroll_for_employee(emp):
        att = [a for a in db.get("attendance", []) if a.get("employeeId") == emp["id"]]
        present_days = len([a for a in att if a.get("status") == "Present"])
        absent_days = len([a for a in att if a.get("status") == "Absent"])
        allowance = round(emp.get("salary", 0) * 0.1)
        deduction = absent_days * 500
        return {
            "employeeId": emp["id"],
            "name": emp["name"],
            "basicSalary": emp.get("salary", 0),
            "presentDays": present_days,
            "absentDays": absent_days,
            "allowance": allowance,
            "deduction": deduction,
            "netSalary": emp.get("salary", 0) + allowance - deduction
        }

    if user["role"] == "employee":
        emp = get_employee_for_user(db, user["id"])
        return jsonify([payroll_for_employee(emp)] if emp else []), 200
    
    return jsonify([payroll_for_employee(e) for e in db.get("employees", [])]), 200

@app.route("/api/jd", methods=["GET", "POST"])
def handle_jd():
    user, err_res, status = require_auth(ROLE_ACCESS["hr"])
    if err_res: return err_res, status
    db = read_db()
    if request.method == "GET":
        return jsonify({"jdText": db.get("jobDescription", "")}), 200
    else:
        body = request.json or {}
        db["jobDescription"] = body.get("jdText", "")
        write_db(db)
        return jsonify({"ok": True}), 200

@app.route("/api/candidates", methods=["GET"])
def get_candidates():
    user, err_res, status = require_auth()
    if err_res: return err_res, status
    if user["role"] not in ROLE_ACCESS["hr"]:
        return jsonify([]), 200
    return jsonify(read_db().get("candidates", [])), 200

def parse_pdf(filepath):
    try:
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error extracting PDF: {str(e)}"

@app.route("/api/candidates", methods=["POST"])
def upload_candidates():
    user, err_res, status = require_auth(ROLE_ACCESS["hr"])
    if err_res: return err_res, status
    db = read_db()
    body = request.json or {}
    resumes = body.get("resumes", [])
    if not isinstance(resumes, list):
        return jsonify({"error": "Resumes must be an array"}), 400

    processed = []
    temp_dir = os.path.join(os.path.dirname(__file__), "temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    for res_data in resumes:
        if not res_data.get("data"): continue
        base64_data = re.sub(r'^data:.*?;base64,', '', res_data["data"])
        ext = ".pdf" if res_data.get("name", "").lower().endswith(".pdf") else ".docx"
        file_path = os.path.join(temp_dir, f"temp_{int(time.time()*1000)}_{os.urandom(4).hex()}{ext}")
        
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(base64_data))
        
        # Native PDF Parsing!
        text = ""
        if ext == ".pdf":
            text = parse_pdf(file_path)
        else:
            text = "DOCX parsing unsupported in minimal Python script without python-docx."
            
        os.remove(file_path)
        
        # AI Extraction
        extracted_name = None
        try:
            name_raw = call_groq(
                "You are a resume parser. Extract only the candidate's full name from the resume text. Return just the name and nothing else — no punctuation, no labels, no explanation.",
                text
            )
            extracted_name = re.sub(r"[^a-zA-Z\s'-]", "", name_raw).strip()
            if not extracted_name: extracted_name = None
        except Exception:
            pass

        active_jd_text = db.get("jobDescription", "").strip() or "AI/ML Fullstack Engineer: React.js, Node.js, Python, MongoDB, PostgreSQL, OpenAI/Claude/Gemini API, TensorFlow, Docker, AWS/GCP, REST APIs, JWT Auth, Git, CI/CD"
        system_prompt = "You are an expert ATS (Applicant Tracking System) and senior HR screener with 15 years of experience. You evaluate resumes against job descriptions with precision and return structured JSON only."
        user_prompt = f"""JOB DESCRIPTION:
{active_jd_text}

CANDIDATE RESUME TEXT:
{text}

Perform a strictly rigorous, multi-stage ATS evaluation.

STAGE 1: STRICT ATS FORMAT & AUTHENTICITY CHECK (Independent of JD)
Examine the resume for:
- Format & Structure: Are there proper section headings? Is the text alignment and structure logical?
- Authenticity & Plagiarism: Does it overuse generic buzzwords or heavily AI-generated phrasing without substance?
- Chronology: Are the dates logical and correct without unexplained gaps?
Score this strictly (atsFormalScore). Penalize heavily for excessive buzzwords, AI-feel, poor alignment, or broken dates.

STAGE 2: RELEVANCY & JD MATCH
Examine the resume against the JD for:
- Direct keyword matches (atsKeywordScore).
- Holistic Relevancy: Does the candidate's actual experience and project depth make them a genuine fit for this specific JD? (jdRelevancyScore).

Return ONLY a valid JSON object with exactly this shape and no other text:
{{
  "candidateName": "<full name extracted from resume text, or null if not clearly present>",
  "atsFormalScore": <integer 0-100: rigorous score of formatting, logical dates, and authenticity. Deduct points heavily for excessive buzzwords, AI-style phrasing, poor alignment, or missing contact info.>,
  "atsKeywordScore": <integer 0-100: strict percentage of essential JD keywords explicitly found in context>,
  "jdRelevancyScore": <integer 0-100: holistic relevancy based on depth of experience and genuine fit, not just keywords>,
  "overallScore": <integer 0-100: weighted score = (atsKeywordScore * 0.30) + (jdRelevancyScore * 0.50) + (atsFormalScore * 0.20), rounded to nearest integer>,
  "matchedKeywords": ["<keyword1>", "<keyword2>"],
  "missingKeywords": ["<keyword1>", "<keyword2>"],
  "recommendation": "<exactly one of the three strings: Shortlisted, Review manually, Needs improvement>",
  "justification": "<2-3 sentences: strict professional explanation of the score, noting any authenticity/buzzword/formatting issues, and why this recommendation was given>",
  "redFlags": ["<concern1>", "<concern2>"]
}}
"""
        try:
            raw = call_groq(system_prompt, user_prompt)
            ai_result = extract_json(raw)
        except Exception as e:
            print("ATS scoring fallback:", e)
            fallback = score_resume_fallback(active_jd_text, text)
            ai_result = {
                "candidateName": None,
                "atsFormalScore": 60,
                "atsKeywordScore": fallback["score"],
                "jdRelevancyScore": fallback["score"],
                "overallScore": fallback["score"],
                "matchedKeywords": fallback.get("matchedSkills", []),
                "missingKeywords": fallback.get("gaps", []),
                "recommendation": "Shortlisted" if fallback["score"] >= 70 else "Review manually" if fallback["score"] >= 45 else "Needs improvement",
                "justification": "Fallback evaluation (Groq AI unavailable). " + fallback["justification"],
                "redFlags": []
            }

        email_match = re.search(r"[\w.-]+@[\w.-]+\.\w+", text) if text else None
        final_name = extracted_name or ai_result.get("candidateName") or res_data.get("name") or "Unknown Candidate"

        candidate = {
            "id": create_id("cand"),
            "name": final_name,
            "email": email_match.group(0) if email_match else res_data.get("email", "no-email@provided.com"),
            "skills": ", ".join(ai_result.get("matchedKeywords", [])) if ai_result.get("matchedKeywords") else "",
            "resumeText": text,
            "atsFormalScore": ai_result.get("atsFormalScore", 0),
            "atsKeywordScore": ai_result.get("atsKeywordScore", 0),
            "jdRelevancyScore": ai_result.get("jdRelevancyScore", 0),
            "aiScore": ai_result.get("overallScore", 0),
            "recommendation": ai_result.get("recommendation", "Review manually"),
            "aiFeedback": ai_result.get("justification", ""),
            "justification": ai_result.get("justification", ""),
            "matchedKeywords": ai_result.get("matchedKeywords", []),
            "missingKeywords": ai_result.get("missingKeywords", []),
            "redFlags": ai_result.get("redFlags", [])
        }
        db.setdefault("candidates", []).append(candidate)
        processed.append(candidate)
        
    write_db(db)
    return jsonify(processed), 201

@app.route("/api/performance", methods=["GET"])
def get_performance():
    user, err_res, status = require_auth()
    if err_res: return err_res, status
    db = read_db()
    if user["role"] == "employee":
        emp = get_employee_for_user(db, user["id"])
        rows = [r for r in db.get("performance", []) if r.get("employeeId") == emp["id"]] if emp else []
        return jsonify(rows), 200
    return jsonify(db.get("performance", [])), 200

@app.route("/api/performance", methods=["POST"])
def create_performance():
    user, err_res, status = require_auth(ROLE_ACCESS["manager"])
    if err_res: return err_res, status
    db = read_db()
    body = request.json or {}
    emp = next((e for e in db.get("employees", []) if e["id"] == body.get("employeeId")), None)
    if not emp: return jsonify({"error": "Employee not found."}), 404
    
    # AI Summary
    ai_summary = ""
    try:
        sys_p = "You are a professional HR performance review writer at FWC IT Services. Write concise, constructive reviews. Respond with ONLY the review text, no JSON or markdown."
        user_p = f"Write a professional performance review summary for {emp['name']} who received a rating of {body.get('rating')}/5.\nManager's feedback: \"{body.get('feedback')}\"\nRequirements:\n- Exactly 3 sentences\n- Professional and constructive tone\n- Acknowledge strengths based on the rating\n- End with one specific, actionable next-step goal\n- Do NOT use bullet points or formatting, just plain sentences"
        ai_summary = call_groq(sys_p, user_p)
    except Exception as e:
        print("Groq performance summary fallback:", e)
        ai_summary = create_performance_summary_fallback(emp['name'], float(body.get('rating', 0)), body.get('feedback', ''))

    review = {
        "id": create_id("perf"),
        "employeeId": body.get("employeeId"),
        "rating": float(body.get("rating", 0)),
        "feedback": body.get("feedback"),
        "aiSummary": ai_summary
    }
    db.setdefault("performance", []).append(review)
    write_db(db)
    return jsonify(review), 201

@app.route("/api/ai/interview-questions", methods=["POST"])
def generate_questions():
    body = request.json or {}
    skills = body.get("skills", "")
    try:
        sys_p = "You are a senior technical interviewer at FWC IT Services. Generate interview questions that test both depth and practical experience. You must respond with ONLY a valid JSON array of strings, no markdown fences or extra text."
        user_p = f"Generate exactly 6 interview questions for a candidate with these skills: {skills or 'general software development'}.\nMix of:\n- 3 technical depth questions\n- 1 practical scenario questions\n- 2 behavioural/situational questions\nReturn a JSON array of 6 question strings: [\"question1\", \"question2\", ...]"
        raw = call_groq(sys_p, user_p)
        questions = extract_json(raw)
        if not isinstance(questions, list): raise Exception("Not a list")
        return jsonify({"questions": questions}), 200
    except Exception as e:
        print("Groq interview questions fallback:", e)
        return jsonify({"questions": create_interview_questions_fallback(skills)}), 200

@app.route("/api/ai/chatbot", methods=["POST"])
@app.route("/api/ai/recruiter-chat", methods=["POST"])
def ai_chatbot():
    user, err_res, status = require_auth()
    if err_res: return err_res, status
    db = read_db()
    body = request.json or {}
    
    if body.get("candidateId"):
        candidate = next((c for c in db.get("candidates", []) if c["id"] == body.get("candidateId")), None)
        if not candidate: return jsonify({"error": "Candidate not found"}), 404
        sys_p = f"You are an FWC Technical Recruiter conducting a screening interview with {candidate['name']}.\nCandidate's skills: {candidate.get('skills', '')}. Try to evaluate them based on those skills.\nKeep your responses short (1-3 sentences). Ask ONE technical or behavioral question at a time.\nEvaluate their previous answer before asking the next question. Start the interview by greeting them if this is the first message."
        user_p = f"Candidate says: \"{body.get('question')}\"" if body.get("question") else "Start the interview."
        try:
            raw = call_groq(sys_p, user_p)
            return jsonify({"answer": raw.strip()}), 200
        except Exception:
            return jsonify({"answer": "Chatbot is temporarily offline."}), 200
    else:
        question = body.get("question", "")
        emp = get_employee_for_user(db, user["id"])
        
        emp_data = f"Your employee record: Name: {emp['name']}, Department: {emp.get('department')}, Designation: {emp.get('designation')}, Salary: Rs. {emp.get('salary')}, Joined: {emp.get('joiningDate')}" if emp else f"You are viewing as {user['role']}. Total employees: {len(db.get('employees', []))}"
        
        leave_data = [l for l in db.get("leaves", []) if l.get("employeeId") == emp["id"]] if emp else db.get("leaves", [])
        leave_context_list = [str(l.get("fromDate")) + " to " + str(l.get("toDate")) + " - " + str(l.get("status")) for l in leave_data]
        leave_context = f"Leave requests ({len(leave_data)} total): {'; '.join(leave_context_list) or 'None'}"
        
        att_data = [a for a in db.get("attendance", []) if a.get("employeeId") == emp["id"]] if emp else db.get("attendance", [])
        pres = len([a for a in att_data if a.get("status") == "Present"])
        absent = len([a for a in att_data if a.get("status") == "Absent"])
        att_context = f"Attendance: {pres} present, {absent} absent out of {len(att_data)} records"
        
        cands_context = ""
        if user["role"] in ["admin", "hr"]:
            cands_list = []
            for c in db.get("candidates", []):
                matched = ", ".join(c.get("matchedKeywords", []) if isinstance(c.get("matchedKeywords"), list) else [])
                cands_list.append(f"ID: {c.get('id')}, Name: {c.get('name')}, Score: {c.get('aiScore')}, Decision: {c.get('recommendation')}, Justification: {c.get('justification')}, Skills: {matched}")
            cands_context = "Candidates in pipeline:\n" + "\n".join(cands_list)

        sys_p = "You are an AI HR assistant at FWC IT Services Pvt. Ltd. You help employees and managers with HR queries. Be helpful, professional, and friendly. Provide concise answers for simple queries, but if the user asks for detailed analysis (e.g. about candidates), provide comprehensive, specific, and to-the-point details using the data provided.\nIf the user asks you to shortlist a candidate, you MUST include this exact tag on a new line: [ACTION: SHORTLIST, candidate_id].\nIf the user asks you to remove, reject, or delete a candidate, you MUST include this exact tag on a new line: [ACTION: REMOVE, candidate_id]."
        user_p = f"HR Data Context:\n{emp_data}\n{leave_context}\n{att_context}\n{cands_context}\nCompany Policies: Standard corporate HR policies apply.\nCurrent user role: {user['role']}\n\nEmployee question: \"{question}\""
        
        try:
            raw = call_groq(sys_p, user_p)
            ans = raw.strip()
            
            # Match actions
            shortlist_match = re.search(r"\[ACTION:\s*SHORTLIST,\s*([^\]]+)\]", ans, re.IGNORECASE)
            if shortlist_match:
                cand_id = shortlist_match.group(1).strip()
                cand = next((c for c in db.get("candidates", []) if c["id"] == cand_id), None)
                if cand:
                    cand["recommendation"] = "Shortlisted"
                    cand["aiDecision"] = "Shortlisted"
                    write_db(db)
            
            remove_match = re.search(r"\[ACTION:\s*REMOVE,\s*([^\]]+)\]", ans, re.IGNORECASE)
            if remove_match:
                cand_id = remove_match.group(1).strip()
                db["candidates"] = [c for c in db.get("candidates", []) if c["id"] != cand_id]
                write_db(db)
                
            ans = re.sub(r"\[ACTION:.*?\]", "", ans, flags=re.IGNORECASE).strip()
            return jsonify({"answer": ans}), 200
        except Exception as e:
            print("Groq HR Chatbot fallback:", e)
            return jsonify({"answer": answer_hr_question_fallback(db, user, question)}), 200

@app.route("/api/ai/attrition-risk", methods=["POST"])
def ai_attrition_risk():
    user, err_res, status = require_auth(ROLE_ACCESS["manager"])
    if err_res: return err_res, status
    db = read_db()
    body = request.json or {}
    emp_id = body.get("employeeId")
    if not emp_id: return jsonify({"error": "employeeId is required"}), 400
    
    emp = next((e for e in db.get("employees", []) if e["id"] == emp_id), None)
    if not emp: return jsonify({"error": "Employee not found"}), 404
    
    att = [a for a in db.get("attendance", []) if a.get("employeeId") == emp_id]
    pres = len([a for a in att if a.get("status") == "Present"])
    att_rate = round((pres / len(att)) * 100) if len(att) > 0 else 100
    
    leaves = [l for l in db.get("leaves", []) if l.get("employeeId") == emp_id]
    leave_count = len(leaves)
    
    perfs = [p for p in db.get("performance", []) if p.get("employeeId") == emp_id]
    avg_rating = round(sum([p.get("rating", 3) for p in perfs]) / len(perfs), 1) if len(perfs) > 0 else 3.0
    
    try:
        jd = datetime.strptime(emp.get("joiningDate", "2026-01-01"), "%Y-%m-%d")
        tenure = max(1, (datetime.now() - jd).days)
    except Exception:
        tenure = 90

    try:
        # In a real app, we'd use Claude if we wanted, but we'll use Groq for everything to simplify dependencies if Claude is not provided
        sys_p = "You are an HR analytics AI at FWC IT Services specialising in employee retention. Analyse employee data to predict attrition risk. Respond with ONLY valid JSON, no markdown fences or extra text."
        user_p = f"Assess attrition risk for this employee:\nName: {emp['name']}\nDepartment: {emp.get('department')}\nMonthly Salary: Rs. {emp.get('salary')}\nTenure: {tenure} days\nAttendance Rate: {att_rate}%\nLeave Requests: {leave_count}\nPerformance Rating: {avg_rating}/5\nReturn JSON exactly in this format:\n{{\"riskLevel\": \"<Low|Medium|High>\", \"factors\": [\"factor1\", \"factor2\", \"factor3\"], \"retentionAction\": \"<one specific action>\", \"confidence\": <number 60-95>}}"
        raw = call_groq(sys_p, user_p)
        result = extract_json(raw)
        return jsonify({
            "riskLevel": result.get("riskLevel", "Medium"),
            "factors": result.get("factors", ["Insufficient data"])[:3],
            "retentionAction": result.get("retentionAction", "Schedule a check-in meeting."),
            "confidence": float(result.get("confidence", 70))
        }), 200
    except Exception as e:
        print("Attrition risk fallback:", e)
        return jsonify(predict_attrition_fallback(emp, att_rate, leave_count, avg_rating, tenure)), 200

@app.route("/api/notifications", methods=["GET"])
def get_notifications():
    user, err_res, status = require_auth()
    if err_res: return err_res, status
    db = read_db()
    emp = get_employee_for_user(db, user["id"])
    notifs = []
    
    if user["role"] in ["admin", "hr", "manager"]:
        pending = [l for l in db.get("leaves", []) if l.get("status") == "Pending"]
        for l in pending[-5:]:
            e = next((x for x in db.get("employees", []) if x["id"] == l.get("employeeId")), None)
            notifs.append({
                "id": f"notif-leave-{l['id']}",
                "type": "leave",
                "title": "Pending Leave Request",
                "message": f"{e['name'] if e else 'Employee'} requested leave from {l.get('fromDate')} to {l.get('toDate')}",
                "date": l.get('fromDate'),
                "read": False
            })
            
    if emp:
        att = [a for a in db.get("attendance", []) if a.get("employeeId") == emp["id"] and a.get("status") == "Absent"]
        for a in att[-3:]:
            notifs.append({
                "id": f"notif-att-{a['id']}",
                "type": "attendance",
                "title": "Attendance Alert",
                "message": f"You were marked absent on {a.get('date')}",
                "date": a.get("date"),
                "read": False
            })
        leaves = [l for l in db.get("leaves", []) if l.get("employeeId") == emp["id"] and l.get("status") != "Pending"]
        for l in leaves[-3:]:
            notifs.append({
                "id": f"notif-lstat-{l['id']}",
                "type": "leave_status",
                "title": f"Leave {l.get('status')}",
                "message": f"Your leave from {l.get('fromDate')} to {l.get('toDate')} was {str(l.get('status')).lower()}",
                "date": l.get("fromDate"),
                "read": False
            })
            
    return jsonify(notifs[-10:]), 200

@app.route("/api/announcements", methods=["GET"])
def get_announcements():
    return jsonify(read_db().get("announcements", [])), 200

@app.route("/api/announcements", methods=["POST"])
def create_announcement():
    user, err_res, status = require_auth(["admin"])
    if err_res: return err_res, status
    db = read_db()
    body = request.json or {}
    if not body.get("title") or not body.get("content"):
        return jsonify({"error": "Title and content are required."}), 400
    ann = {
        "id": create_id("ann"),
        "title": body.get("title"),
        "content": body.get("content"),
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "createdBy": user["name"]
    }
    db.setdefault("announcements", []).append(ann)
    write_db(db)
    return jsonify(ann), 201

# --- Static File Routing ---

@app.route("/", defaults={"path": "index.html"})
@app.route("/<path:path>")
def serve_static(path):
    if not os.path.exists(os.path.join(app.static_folder, path)):
        abort(404)
    return send_from_directory(app.static_folder, path)

if __name__ == "__main__":
    print(f"FWC AI HRMS (Python/Flask) running at http://localhost:{PORT}")
    if GROQ_API_KEY:
        print("[OK] Groq AI features enabled (API key detected)")
    else:
        print("[WARN] Groq API key not set — AI features will use rule-based fallback")
        
    read_db() # initialize
    app.run(host="0.0.0.0", port=PORT, threaded=True)
