@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

:: ==============================================================================
::  mcp-adk-agent — Windows Runner
:: ==============================================================================

set "VENV=.venv"
set "PYTHON=%VENV%\Scripts\python.exe"
set "PIP=%VENV%\Scripts\pip.exe"
set "ADK=%VENV%\Scripts\adk.exe"

if "%~1"=="" goto help
if /i "%~1"=="setup" goto setup
if /i "%~1"=="auth" goto auth
if /i "%~1"=="run" goto run
if /i "%~1"=="cli" goto cli
if /i "%~1"=="clean" goto clean
goto help

:help
echo.
echo  mcp-adk-agent (Windows Runner)
echo.
echo  Available commands:
echo    windows_runner.bat setup  - create Python venv + install deps + copy .env
echo    windows_runner.bat auth   - Google Cloud authentication (ADC)
echo    windows_runner.bat run    - start web interface -^> http://localhost:8000
echo    windows_runner.bat cli    - start CLI interface (terminal)
echo    windows_runner.bat clean  - remove .venv and Python caches
echo.
goto :eof

:setup
echo 📦 Checking venv and installing dependencies...
if not exist "%VENV%\Scripts\activate.bat" (
    echo Creating Python venv...
    python -m venv "%VENV%"
)
"%PIP%" install --quiet --upgrade pip
"%PIP%" install --upgrade -r requirements.txt

if not exist ".env" (
    if exist ".env.example" (
        echo 📋 Copying .env.example -^> .env
        copy .env.example .env
        echo   ⚠️  Check values in .env if necessary.
    ) else (
        echo ⚠️  .env.example not found. Creating an empty .env...
        echo MCP_API_KEY=> .env
    )
)
echo ✅ Setup complete.
goto :eof

:auth
echo 🔐 Google Cloud Authentication...
call gcloud auth application-default login
echo ✅ Authentication complete.
goto :eof

:run
call :setup
echo.
echo 🔐 Checking Google Cloud credentials...
"%PYTHON%" -c "import google.auth, google.auth.transport.requests; creds, p = google.auth.default(scopes=['openid','https://www.googleapis.com/auth/cloud-platform']); creds.refresh(google.auth.transport.requests.Request()); print('✅ Credentials valid for project:', p)" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ❌ Credentials expired or missing. Launching authentication...
    echo.
    call :auth
)
echo.
echo 🚀 Starting ADK agent -^> http://localhost:8000
"%ADK%" web --log_level DEBUG .
goto :eof

:cli
call :setup
echo 🚀 Starting CLI mode...
"%ADK%" run test_agent
goto :eof

:clean
echo 🧹 Removing venv and caches...
if exist "%VENV%" rmdir /s /q "%VENV%"
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
del /s /q *.pyc >nul 2>&1
echo ✅ Cleanup complete.
goto :eof