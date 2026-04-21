@echo off
cd /d "%~dp0backend"

:: Buscar Python (instalacion normal o py launcher)
where python >nul 2>&1 && set PYTHON=python && goto :found
where py >nul 2>&1 && set PYTHON=py && goto :found
echo.
echo  ERROR: Python no esta instalado.
echo  Descarga Python desde https://www.python.org/downloads/
echo  Marca "Add Python to PATH" durante la instalacion.
echo.
pause
exit /b 1

:found
:: Crear venv si no existe
if not exist "venv\Scripts\activate.bat" (
    echo Creando entorno virtual...
    %PYTHON% -m venv venv
)

:: Activar venv e instalar dependencias
call venv\Scripts\activate.bat
pip install -r requirements.txt -q

:: Iniciar uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
