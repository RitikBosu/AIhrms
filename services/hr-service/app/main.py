from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_db_and_tables
from app.routers import auth, employees, attendance, leaves, payroll, performance, dashboard, audit, shifts, scheduling
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="FWC HRMS — HR Service", version="2.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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


app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])
app.include_router(employees.router, prefix="/api", tags=["Employees"])
app.include_router(attendance.router, prefix="/api", tags=["Attendance"])
app.include_router(leaves.router, prefix="/api", tags=["Leaves"])
app.include_router(payroll.router, prefix="/api", tags=["Payroll"])
app.include_router(performance.router, prefix="/api", tags=["Performance"])
app.include_router(audit.router, prefix="/api", tags=["Audit"])
app.include_router(shifts.router, prefix="/api", tags=["Shifts"])
app.include_router(scheduling.router, prefix="/api", tags=["Scheduling"])

@app.get("/")
def root():
    return {"service": "HR Service", "status": "running"}
