@echo off
echo === SUZANO DASHBOARD ===
echo.

cd /d "%~dp0"

echo Ativando ambiente Python...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo Criando ambiente virtual...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
)

echo.
echo Coletando dados da API Creare...
python scripts\collect_data.py

echo.
echo Iniciando servidor dashboard...
echo Dashboard: http://localhost:8000/dashboard
echo API Docs: http://localhost:8000/docs
echo.

cd backend
python main.py

pause
