# Convenience script to start all SportX dev processes in separate windows.
# Requires MongoDB running locally. Run from the repository root.

$root = Split-Path -Parent $PSScriptRoot

Write-Host "Starting SportX development stack..." -ForegroundColor Cyan

# Backend
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$root\backend'; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8000"
)

# User frontend
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$root\frontend-user'; npm run dev"
)

# Admin frontend
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$root\frontend-admin'; npm run dev"
)

Write-Host "Backend:        http://localhost:8000/docs" -ForegroundColor Green
Write-Host "User frontend:  http://localhost:5173" -ForegroundColor Green
Write-Host "Admin frontend: http://localhost:5174" -ForegroundColor Green
