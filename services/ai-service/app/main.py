from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_db_and_tables
from app.routers import candidates

app = FastAPI(title="FWC HRMS — AI Screening Service", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


app.include_router(candidates.router, prefix="/api", tags=["Candidates"])


@app.get("/")
def root():
    return {"service": "AI Screening Service", "status": "running"}
