"""
Seed script — migrates existing db.json candidates into Neon AI DB.
Run once from: services/ai-service/
  python -m app.seed
"""
import os
import json
import sys

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))

from sqlmodel import Session, select
from app.database import engine, create_db_and_tables
from app.models import Candidate, JobDescription

DB_JSON = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "backend", "data", "db.json"
)


def seed():
    print("[seed] Creating AI tables...")
    create_db_and_tables()

    if not os.path.exists(DB_JSON):
        print(f"[ERROR] db.json not found at {DB_JSON}")
        sys.exit(1)

    with open(DB_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    with Session(engine) as session:
        # ── Job Description ────────────────────────────────────────────────
        jd_text = data.get("jobDescription", "")
        if jd_text:
            existing = session.exec(select(JobDescription)).first()
            if not existing:
                session.add(JobDescription(jd_text=jd_text))
                session.commit()
                print(f"  [OK] Job description seeded ({len(jd_text)} chars)")

        # ── Candidates ─────────────────────────────────────────────────────
        cand_count = 0
        for c in data.get("candidates", []):
            existing = session.exec(select(Candidate).where(Candidate.legacy_id == c.get("id"))).first()
            if existing:
                continue
            session.add(Candidate(
                legacy_id=c.get("id"),
                name=c.get("name", "Unknown"),
                email=c.get("email", ""),
                filename=c.get("filename", ""),
                ai_score=float(c.get("aiScore", 0)),
                ai_decision=c.get("aiDecision", "Review manually"),
                matched_skills=json.dumps(c.get("matchedSkills", [])),
                gaps=json.dumps(c.get("gaps", [])),
                justification=c.get("justification", ""),
                uploaded_at=c.get("uploadedAt", ""),
            ))
            cand_count += 1

        session.commit()
        print(f"  [OK] Candidates seeded: {cand_count}")

    print("\n[DONE] AI service seeding complete!")


if __name__ == "__main__":
    seed()
