@echo off
echo ============================================
echo  GymSystem Pro - Backend (FastAPI)
echo ============================================
cd /d "%~dp0backend"

if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
)

call venv\Scripts\activate

echo Instalando dependencias...
pip install -r requirements.txt -q

echo.
echo Iniciando servidor en http://localhost:8001
echo Documentacion API: http://localhost:8001/api/docs
echo.
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
pause
