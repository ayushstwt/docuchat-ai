# PowerShell script to start DocuChat AI Backend and Frontend concurrently
$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host " Starting DocuChat AI (Backend + Frontend)" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# 1. Determine Python / Uvicorn executable
$VenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    $VenvPython = "python"
}

# 2. Start Backend Process
Write-Host "[Backend] Starting FastAPI server on http://localhost:8000..." -ForegroundColor Green
$BackendProcess = Start-Process -FilePath $VenvPython `
    -ArgumentList "-m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" `
    -WorkingDirectory $BackendDir `
    -PassThru

# 3. Start Frontend Process
Write-Host "[Frontend] Starting Vite dev server on http://localhost:5173..." -ForegroundColor Green
$NpmCmd = if (Get-Command "npm.cmd" -ErrorAction SilentlyContinue) { "npm.cmd" } else { "npm" }
$FrontendProcess = Start-Process -FilePath $NpmCmd `
    -ArgumentList "run dev" `
    -WorkingDirectory $FrontendDir `
    -PassThru

Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host " DocuChat AI Dev Environment is running!" -ForegroundColor Cyan
Write-Host " - Backend API docs: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host " - Frontend Web UI:  http://localhost:5173" -ForegroundColor Yellow
Write-Host " Press Ctrl+C in this window to stop both servers." -ForegroundColor Gray
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

try {
    # Keep script alive and monitor child processes
    while (-not $BackendProcess.HasExited -and -not $FrontendProcess.HasExited) {
        Start-Sleep -Seconds 1
    }
}
finally {
    Write-Host "`n[Dev] Shutting down backend and frontend processes..." -ForegroundColor Yellow
    if ($BackendProcess -and -not $BackendProcess.HasExited) {
        Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($FrontendProcess -and -not $FrontendProcess.HasExited) {
        Stop-Process -Id $FrontendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "[Dev] Clean shutdown complete." -ForegroundColor Green
}
