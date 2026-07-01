import os
import re
import time
import base64
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from PyPDF2 import PdfReader

from app.routers.deps import get_current_user
from app.services.db import read_db, write_db
from app.services.ai_utils import call_groq, extract_json, score_resume_fallback

router = APIRouter()

ROLE_ACCESS = {
    "hr": ["admin", "hr"]
}

def require_role(user, allowed_roles):
    if user["role"] not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission for this action.")

def create_id(prefix):
    return f"{prefix}-{int(time.time()*1000)}-{os.urandom(3).hex()}"

class ResumeUpload(BaseModel):
    name: str
    data: str

class CandidatesUpload(BaseModel):
    resumes: List[ResumeUpload]

class JDUpdate(BaseModel):
    jdText: str

def parse_pdf(filepath):
    try:
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error extracting PDF: {str(e)}"

@router.get("/candidates")
def get_candidates(user: dict = Depends(get_current_user)):
    if user["role"] not in ROLE_ACCESS["hr"]:
        return []
    return read_db().get("candidates", [])

@router.get("/jd")
def get_jd(user: dict = Depends(get_current_user)):
    require_role(user, ROLE_ACCESS["hr"])
    return {"jdText": read_db().get("jobDescription", "")}

@router.post("/jd")
def update_jd(jd_in: JDUpdate, user: dict = Depends(get_current_user)):
    require_role(user, ROLE_ACCESS["hr"])
    db = read_db()
    db["jobDescription"] = jd_in.jdText
    write_db(db)
    return {"ok": True}

@router.post("/candidates")
def upload_candidates(candidates_in: CandidatesUpload, user: dict = Depends(get_current_user)):
    require_role(user, ROLE_ACCESS["hr"])
    db = read_db()
    resumes = candidates_in.resumes
    
    processed = []
    temp_dir = os.path.join(os.path.dirname(__file__), "..", "temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    for res_data in resumes:
        if not res_data.data: continue
        base64_data = re.sub(r'^data:.*?;base64,', '', res_data.data)
        ext = ".pdf" if res_data.name.lower().endswith(".pdf") else ".docx"
        file_path = os.path.join(temp_dir, f"temp_{int(time.time()*1000)}_{os.urandom(4).hex()}{ext}")
        
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(base64_data))
        
        text = ""
        if ext == ".pdf":
            text = parse_pdf(file_path)
        else:
            text = "DOCX parsing unsupported in minimal Python script without python-docx."
            
        os.remove(file_path)
        
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
        system_prompt = "You are an expert ATS (Applicant Tracking System) and senior HR screener. You evaluate resumes against job descriptions and return structured JSON only."
        user_prompt = f"""JOB DESCRIPTION:\n{active_jd_text}\n\nCANDIDATE RESUME TEXT:\n{text}\n\nPerform a strictly rigorous ATS evaluation. Return exactly this JSON format:
{{
  "candidateName": "<name>",
  "overallScore": <integer 0-100>,
  "matchedKeywords": ["<kw1>"],
  "missingKeywords": ["<kw1>"],
  "recommendation": "<Shortlisted, Review manually, Needs improvement>",
  "justification": "<2-3 sentences>"
}}"""
        try:
            raw = call_groq(system_prompt, user_prompt)
            ai_result = extract_json(raw)
        except Exception as e:
            print("ATS scoring fallback:", e)
            fallback = score_resume_fallback(active_jd_text, text)
            ai_result = {
                "candidateName": None,
                "overallScore": fallback["score"],
                "matchedKeywords": fallback.get("matchedSkills", []),
                "missingKeywords": fallback.get("gaps", []),
                "recommendation": fallback["decision"],
                "justification": "Fallback evaluation (Groq AI unavailable). " + fallback["justification"]
            }

        email_match = re.search(r"[\w.-]+@[\w.-]+\.\w+", text) if text else None
        final_name = extracted_name or ai_result.get("candidateName") or res_data.name or "Unknown Candidate"
        
        candidate = {
            "id": create_id("cand"),
            "name": final_name,
            "email": email_match.group(0) if email_match else "Not found",
            "filename": res_data.name,
            "aiScore": ai_result.get("overallScore", 0),
            "aiDecision": ai_result.get("recommendation", "Review manually"),
            "matchedSkills": ai_result.get("matchedKeywords", []),
            "gaps": ai_result.get("missingKeywords", []),
            "justification": ai_result.get("justification", ""),
            "uploadedAt": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        db.setdefault("candidates", []).append(candidate)
        processed.append(candidate)
        
    write_db(db)
    return {"processed": len(processed), "candidates": processed}
