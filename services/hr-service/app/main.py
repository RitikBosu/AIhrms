from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_db_and_tables
from app.routers import auth, employees, attendance, leaves, payroll, performance, dashboard

app = FastAPI(title="FWC HRMS — HR Service", version="2.0.0")

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


@app.get("/")
def root():
    return {"service": "HR Service", "status": "running"}
