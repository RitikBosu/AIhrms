import os
import re
import time
import base64
import json
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import List, Optional
from sqlmodel import Session, select
from PyPDF2 import PdfReader

from app.database import get_session
from app.models import Candidate, JobDescription
from app.routers.deps import get_current_user
from app.services.ai_utils import call_groq, extract_json, score_resume_fallback

router = APIRouter()

TEMP_DIR = os.path.join(os.path.dirname(__file__), "..", "temp")

def require_hr(user):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

class JDUpdate(BaseModel):
    jdText: str

def _parse_pdf(filepath: str) -> str:
    try:
        reader = PdfReader(filepath)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        return f"Error extracting PDF: {e}"

# ── Job Description ──────────────────────────────────────────────────────────

@router.get("/jd")
def get_jd(session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    require_hr(user)
    jd = session.exec(select(JobDescription)).first()
    return {"jdText": jd.jd_text if jd else ""}


@router.post("/jd")
def update_jd(jd_in: JDUpdate, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    require_hr(user)
    jd = session.exec(select(JobDescription)).first()
    if jd:
        jd.jd_text = jd_in.jdText
        jd.updated_at = time.strftime("%Y-%m-%d %H:%M:%S")
    else:
        jd = JobDescription(jd_text=jd_in.jdText, updated_at=time.strftime("%Y-%m-%d %H:%M:%S"))
    session.add(jd)
    session.commit()
    return {"ok": True}


# ── Candidates ───────────────────────────────────────────────────────────────

@router.get("/candidates")
def get_candidates(skip: int = 0, limit: int = 100, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    require_hr(user)
    candidates = session.exec(select(Candidate).offset(skip).limit(limit)).all()
    return [_serialize(c) for c in candidates]


@router.post("/candidates")
@limiter.limit("5/minute")
async def upload_candidates(request: Request, files: List[UploadFile] = File(...), session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    require_hr(user)
    os.makedirs(TEMP_DIR, exist_ok=True)

    jd_row = session.exec(select(JobDescription)).first()
    active_jd = (jd_row.jd_text.strip() if jd_row else "") or \
        "AI/ML Fullstack Engineer: React.js, Node.js, Python, MongoDB, PostgreSQL, Groq AI, Docker, AWS, REST APIs, JWT Auth, Git"

    processed = []
    for file in files:
        ext = ".pdf" if file.filename.lower().endswith(".pdf") else ".docx"
        tmp_path = os.path.join(TEMP_DIR, f"tmp_{int(time.time()*1000)}_{os.urandom(4).hex()}{ext}")

        text = ""
        try:
            content = await file.read()
            with open(tmp_path, "wb") as f:
                f.write(content)

            if ext == ".pdf":
                text = await run_in_threadpool(_parse_pdf, tmp_path)
            else:
                text = "DOCX parsing not supported."
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

        # AI scoring
        system_prompt = "You are an expert ATS screener. Evaluate resumes against job descriptions and return structured JSON only."
        user_prompt = f"JOB DESCRIPTION:\n{active_jd}\n\nRESUME:\n{text}\n\nReturn exactly this JSON:\n{{\n  \"candidateName\": \"<name or null>\",\n  \"overallScore\": <0-100>,\n  \"matchedKeywords\": [\"kw1\"],\n  \"missingKeywords\": [\"kw1\"],\n  \"recommendation\": \"<Shortlisted|Review manually|Needs improvement>\",\n  \"justification\": \"<2-3 sentences>\"\n}}"
        try:
            raw = await run_in_threadpool(call_groq, system_prompt, user_prompt)
            ai_result = extract_json(raw)
        except Exception as e:
            print("ATS fallback:", e)
            fb = score_resume_fallback(active_jd, text)
            ai_result = {
                "candidateName": None,
                "overallScore": fb["score"],
                "matchedKeywords": fb.get("matchedSkills", []),
                "missingKeywords": fb.get("gaps", []),
                "recommendation": fb["decision"],
                "justification": "Fallback: " + fb["justification"],
            }

        email_match = re.search(r"[\w.-]+@[\w.-]+\.\w+", text or "")
        candidate = Candidate(
            name=ai_result.get("candidateName") or file.filename,
            email=email_match.group(0) if email_match else "Not found",
            filename=file.filename,
            ai_score=ai_result.get("overallScore", 0),
            ai_decision=ai_result.get("recommendation", "Review manually"),
            matched_skills=json.dumps(ai_result.get("matchedKeywords", [])),
            gaps=json.dumps(ai_result.get("missingKeywords", [])),
            justification=ai_result.get("justification", ""),
            uploaded_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        )
        session.add(candidate)
        processed.append(candidate)

    session.commit()
    for c in processed:
        session.refresh(c)

    return {"processed": len(processed), "candidates": [_serialize(c) for c in processed]}


def _serialize(c: Candidate) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "email": c.email,
        "filename": c.filename,
        "aiScore": c.ai_score,
        "aiDecision": c.ai_decision,
        "matchedSkills": json.loads(c.matched_skills or "[]"),
        "gaps": json.loads(c.gaps or "[]"),
        "justification": c.justification,
        "uploadedAt": c.uploaded_at,
    }
