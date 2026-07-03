# start.ps1 - Start all HRMS services locally
# Usage: .\start.ps1

$venv = "d:\HRMS\.venv\Scripts\python.exe"
$root = "d:\HRMS"

Write-Host ""
Write-Host "Starting HRMS microservices..." -ForegroundColor Cyan

# Start HR Service (port 8001)
Write-Host "  [1/2] HR Service    -> http://localhost:8001" -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$root\services\hr-service'; & '$venv' -m uvicorn app.main:app --port 8001 --host 0.0.0.0`""

# Brief pause so ports don't collide on startup
Start-Sleep -Seconds 1

# Start AI Service (port 8002)
Write-Host "  [2/2] AI Service    -> http://localhost:8002" -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$root\services\ai-service'; & '$venv' -m uvicorn app.main:app --port 8002 --host 0.0.0.0`""

Write-Host ""
Write-Host "Both services started in separate windows." -ForegroundColor Cyan
Write-Host "Start Next.js separately:  cd next-frontend; npm run dev" -ForegroundColor Yellow
Write-Host ""
