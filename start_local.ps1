# Project Sentinel - Local Run Script (No Docker)
# Run this from d:\Projects\hackathon
# Requires: Python 3.9+, Ollama installed (optional, mock fallback available)

param(
    [switch]$SkipInstall,
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

Write-Host "
+----------------------------------------------+
|      Project Sentinel - Local Launcher       |
|            SQLite + In-Memory Mode           |
+----------------------------------------------+
" -ForegroundColor Cyan

# -- Step 1: Check Python ----------------------------------------------------
Write-Host "[1/5] Checking Python (3.9 - 3.15)..." -ForegroundColor Yellow
$pythonCmd = $null

# Look in common/stable Python install locations on Windows to prefer versions with precompiled wheels (3.11, 3.12)
$commonPaths = @(
    "$env:LocalAppData\Programs\Python\Python312\python.exe",
    "$env:LocalAppData\Programs\Python\Python311\python.exe",
    "$env:LocalAppData\Programs\Python\Python313\python.exe",
    "C:\Python312\python.exe",
    "C:\Python311\python.exe",
    "C:\Python313\python.exe"
)

$searchList = @()
foreach ($p in $commonPaths) {
    if (Test-Path $p) {
        $searchList += $p
    }
}
$searchList += @("python3", "python")

foreach ($cmd in $searchList) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "3\.(9|1[0-5])") {
            $pythonCmd = $cmd
            Write-Host "  [OK] Found: $ver (at $cmd)" -ForegroundColor Green
            break
        }
    } catch {}
}
if (-not $pythonCmd) {
    Write-Host "  [FAIL] Python (3.9 - 3.15) not found. Download from https://python.org" -ForegroundColor Red
    exit 1
}

# -- Step 2: Check Ollama ----------------------------------------------------
Write-Host "[2/5] Checking Ollama..." -ForegroundColor Yellow
try {
    $ollamaStatus = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 3 -ErrorAction SilentlyContinue
    Write-Host "  [OK] Ollama is running." -ForegroundColor Green
} catch {
    Write-Host "  [WARN] Ollama is not running. Starting it..." -ForegroundColor Yellow
    try {
        Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 3
        Write-Host "  [OK] Ollama started." -ForegroundColor Green
    } catch {
        Write-Host "  [WARN] Ollama not found. The app will run in Mock LLM Mode (no server required)." -ForegroundColor Yellow
        Write-Host "     To use real AI analysis later, install Ollama from: https://ollama.com/download" -ForegroundColor Gray
    }
}

# -- Step 3: Create/activate virtual environment ------------------------------
Write-Host "[3/5] Setting up Python virtual environment..." -ForegroundColor Yellow
$venvPath = Join-Path $ProjectRoot ".venv"

if (-not (Test-Path $venvPath)) {
    Write-Host "  Creating venv..." -ForegroundColor Gray
    & $pythonCmd -m venv $venvPath
}

$pip = Join-Path $venvPath "Scripts\pip.exe"
$pythonExe = Join-Path $venvPath "Scripts\python.exe"

# -- Step 4: Install dependencies ---------------------------------------------
if (-not $SkipInstall) {
    Write-Host "[4/5] Installing backend dependencies..." -ForegroundColor Yellow
    & $pip install -r (Join-Path $ProjectRoot "backend\requirements.txt") -q
    Write-Host "  Installing frontend dependencies..." -ForegroundColor Gray
    & $pip install -r (Join-Path $ProjectRoot "frontend\requirements.txt") -q
    Write-Host "  [OK] Dependencies installed." -ForegroundColor Green
} else {
    Write-Host "[4/5] Skipping dependency install (-SkipInstall flag)." -ForegroundColor Gray
}

# -- Step 5: Copy local env ---------------------------------------------------
Write-Host "[5/5] Configuring environment..." -ForegroundColor Yellow
$envTarget = Join-Path $ProjectRoot ".env"
if (-not (Test-Path $envTarget)) {
    Copy-Item (Join-Path $ProjectRoot ".env.local") $envTarget
    Write-Host "  [OK] Created .env from .env.local (LOCAL_MODE=true)" -ForegroundColor Green
} else {
    Write-Host "  [OK] Using existing .env" -ForegroundColor Green
}

Write-Host ""
Write-Host "===============================================" -ForegroundColor DarkGray
Write-Host " Starting Services..." -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor DarkGray

# -- Launch Backend ----------------------------------------------------------
if (-not $FrontendOnly) {
    Write-Host ""
    Write-Host "  * Starting FastAPI backend on http://localhost:8000 ..." -ForegroundColor Cyan
    $backendScript = {
        param($pythonExe, $projectRoot)
        Set-Location $projectRoot
        & $pythonExe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
    }
    $backendJob = Start-Job -ScriptBlock $backendScript -ArgumentList $pythonExe, $ProjectRoot
    Start-Sleep -Seconds 4
}

# -- Launch Frontend ---------------------------------------------------------
if (-not $BackendOnly) {
    Write-Host "  * Starting Streamlit frontend on http://localhost:8501 ..." -ForegroundColor Cyan
    $frontendScript = {
        param($pythonExe, $projectRoot)
        Set-Location (Join-Path $projectRoot "frontend")
        & $pythonExe -m streamlit run app.py --server.port 8501 --server.address localhost --server.headless true
    }
    $frontendJob = Start-Job -ScriptBlock $frontendScript -ArgumentList $pythonExe, $ProjectRoot
}

Write-Host ""
Write-Host "===============================================" -ForegroundColor DarkGray
Write-Host " [OK] Project Sentinel is running!" -ForegroundColor Green
Write-Host ""
Write-Host "   Frontend  -->  http://localhost:8501" -ForegroundColor White
Write-Host "   Backend   -->  http://localhost:8000" -ForegroundColor White
Write-Host "   API Docs  -->  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "   Login: analyst / sentinelpass" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Press Ctrl+C to stop all services." -ForegroundColor DarkGray
Write-Host "===============================================" -ForegroundColor DarkGray

# Keep script alive, forward background job output
try {
    while ($true) {
        if (-not $FrontendOnly -and $backendJob) {
            Receive-Job $backendJob -ErrorAction SilentlyContinue
        }
        if (-not $BackendOnly -and $frontendJob) {
            Receive-Job $frontendJob -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 2
    }
} finally {
    Write-Host "Stopping services..." -ForegroundColor Yellow
    if ($backendJob)  { Stop-Job $backendJob;  Remove-Job $backendJob }
    if ($frontendJob) { Stop-Job $frontendJob; Remove-Job $frontendJob }
}
