from typing import Optional, List
from sqlmodel import Field, SQLModel, Column
import sqlalchemy as sa
import json


# ─── Job Description ─────────────────────────────────────────────────────────

class JobDescription(SQLModel, table=True):
    __tablename__ = "job_descriptions"

    id: Optional[int] = Field(default=None, primary_key=True)
    jd_text: str = Field(default="")
    updated_at: Optional[str] = Field(default=None)


# ─── Candidate ────────────────────────────────────────────────────────────────

class Candidate(SQLModel, table=True):
    __tablename__ = "candidates"

    id: Optional[int] = Field(default=None, primary_key=True)
    legacy_id: Optional[str] = Field(default=None, index=True)
    name: str
    email: Optional[str] = Field(default=None)
    filename: Optional[str] = Field(default=None)
    ai_score: Optional[float] = Field(default=0)
    ai_decision: Optional[str] = Field(default="Review manually")
    # JSON arrays stored as text
    matched_skills: Optional[str] = Field(default="[]")
    gaps: Optional[str] = Field(default="[]")
    justification: Optional[str] = Field(default=None)
    uploaded_at: Optional[str] = Field(default=None)
