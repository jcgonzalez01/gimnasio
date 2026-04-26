@echo off
title Monitor Hikvision - GymSystem
cd /d "%~dp0"
if exist backend\venv (
    call backend\venv\Scripts\activate
)
python monitor_events.py
pause