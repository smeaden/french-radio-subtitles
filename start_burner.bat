@echo off
powershell -NoExit -Command "$host.UI.RawUI.BackgroundColor='DarkRed'; $host.UI.RawUI.ForegroundColor='White'; cls; Write-Host '=== BURNER ===' -ForegroundColor Yellow; python burner.py"