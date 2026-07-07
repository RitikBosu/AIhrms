import os
import requests
import re
import json

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

def call_groq(system_prompt: str, user_prompt: str) -> str:
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

def extract_json(text: str) -> dict:
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
    return {
        "riskLevel": risk_level,
        "riskScore": risk_score,
        "contributingFactors": factors,
        "recommendedAction": "Schedule 1-on-1 check-in" if risk_score >= 25 else "Monitor"
    }

def generate_roster_prompt(prompt: str, start_date: str, end_date: str, context: dict) -> list:
    """
    Calls Groq to generate a draft schedule.
    Context contains masked employee IDs (e.g. EMP_12) to prevent PII leakage.
    Returns a list of dicts: {"employee_id": int, "start_time": iso, "end_time": iso, "title": str}
    """
    sys_prompt = (
        "You are an expert HR workforce scheduling AI. "
        "Your job is to parse the user's natural language scheduling request and output a structured JSON array. "
        "You MUST ONLY output raw JSON. Do not include markdown formatting or explanations.\n"
        "Input context includes a list of available employee IDs (e.g. EMP_1, EMP_2).\n"
        f"Schedule date range: {start_date} to {end_date}.\n\n"
        "Expected JSON Output Format:\n"
        "[\n"
        '  {"employee_id": 1, "start_time": "2026-07-06T09:00:00Z", "end_time": "2026-07-06T17:00:00Z", "title": "Morning Shift"}\n'
        "]"
    )
    
    user_prompt = f"User Request: {prompt}\nContext: {json.dumps(context)}"
    
    try:
        response_text = call_groq(sys_prompt, user_prompt)
        return extract_json(response_text)
    except Exception as e:
        print(f"Groq API Error generating roster: {e}")
        # Fallback to simple stub to let the Deterministic Validator handle it, or just return empty
        return []
