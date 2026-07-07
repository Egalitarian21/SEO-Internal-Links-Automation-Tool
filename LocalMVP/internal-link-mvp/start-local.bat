@echo off
set "ROOT=%~dp0"
start "" powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%ROOT%scripts\launch-hidden.ps1" -ProjectRoot "%ROOT%."
exit /b 0
