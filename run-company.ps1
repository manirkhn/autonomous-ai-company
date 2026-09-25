Write-Host "====================================================" -ForegroundColor Cyan
Write-Host " Starting Autonomous AI Company Gateway..." -ForegroundColor Green
Write-Host " Owner Command Center: http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "====================================================" -ForegroundColor Cyan

Set-Location $PSScriptRoot
python main.py
