@echo off
echo ============================================
echo  GymSystem Pro - Iniciando todo el sistema
echo ============================================
echo.

start "Backend - GymSystem" cmd /k "cd /d "%~dp0backend" && (if not exist venv python -m venv venv) && call venv\Scripts\activate && pip install -r requirements.txt -q && uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"

timeout /t 4 /nobreak >nul

start "Monitor Hikvision - GymSystem" cmd /k "cd /d "%~dp0" && title Monitor de Eventos && (if exist backend\venv call backend\venv\Scripts\activate) && python monitor_events.py"

timeout /t 2 /nobreak >nul

start "Frontend - GymSystem" cmd /k "cd /d "%~dp0frontend" && (if not exist node_modules npm install) && npm run dev"

timeout /t 5 /nobreak >nul

echo Abriendo navegador...
start http://localhost:5173

echo.
echo Sistema iniciado!
echo Backend:  http://localhost:8001
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8001/api/docs
echo Monitor Hikvision: Corriendo en otra ventana
echo.
pause
