from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, dashboard, employees, attendance, leaves, payroll, candidates, performance

app = FastAPI(title="FWC AI-HRMS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])
app.include_router(employees.router, prefix="/api", tags=["Employees"])
app.include_router(attendance.router, prefix="/api", tags=["Attendance"])
app.include_router(leaves.router, prefix="/api", tags=["Leaves"])
app.include_router(payroll.router, prefix="/api", tags=["Payroll"])
app.include_router(candidates.router, prefix="/api", tags=["Candidates"])
app.include_router(performance.router, prefix="/api", tags=["Performance"])

@app.get("/")
def read_root():
    return {"message": "Welcome to FWC AI-HRMS API"}
