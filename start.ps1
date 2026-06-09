# Start restaurant API on port 8080 (avoids conflict with other apps on 8000)
Set-Location $PSScriptRoot
if (-not (Test-Path ".\venv\Scripts\uvicorn.exe")) {
    Write-Error "Run: python -m venv venv; .\venv\Scripts\pip install -r requirements.txt"
    exit 1
}
if (-not (Test-Path ".\data\menu.json")) {
    .\venv\Scripts\python scripts\seed_data.py
}
.\venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
