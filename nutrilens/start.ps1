Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  NutriLens - Automated Food Label Analyser" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Starting Backend  -> http://localhost:8000" -ForegroundColor Yellow
Write-Host "  Starting Frontend -> http://localhost:5173" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Press Ctrl+C to stop both servers." -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot
npm run dev
