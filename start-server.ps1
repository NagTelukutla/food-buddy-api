# Stop leftover backend workers, then start a single API server.
Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -like '*restaurant-app*uvicorn*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

Set-Location $PSScriptRoot
Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique |
  ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }

Write-Host "Starting API on http://127.0.0.1:8080 ..."
& ".\venv\Scripts\uvicorn.exe" app.main:app --host 127.0.0.1 --port 8080
