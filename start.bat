@echo off
rem One-click start: backend on 8000, frontend on 5173
rem Edit PY / NODE below if the toolchain paths change on another machine.
setlocal

set "ROOT=%~dp0"
set "PY=C:\Users\34908\.workbuddy\binaries\python\versions\3.13.12\python.exe"
set "NODE=C:\Users\34908\.workbuddy\binaries\node\versions\22.22.2-6\node.exe"

if not exist "%PY%" (
  echo [ERROR] python not found: %PY%
  echo Edit PY in start.bat first.
  pause
  exit /b 1
)
if not exist "%NODE%" (
  echo [ERROR] node not found: %NODE%
  echo Edit NODE in start.bat first.
  pause
  exit /b 1
)

echo Starting backend  -^> http://127.0.0.1:8000/docs
start "tk-backend" /d "%ROOT%backend" "%PY%" run.py

echo Starting frontend -^> http://localhost:5173
start "tk-frontend" /d "%ROOT%frontend" "%NODE%" "node_modules\vite\bin\vite.js"

timeout /t 5 >nul
start "" http://localhost:5173

endlocal
