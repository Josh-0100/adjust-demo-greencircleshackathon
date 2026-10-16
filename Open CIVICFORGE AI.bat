@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title Adjust AI
set "APP_PYTHON="
set "APP_PYTHON_ARGS="

if defined CIVICFORGE_PYTHON (
    call :choose_python "%CIVICFORGE_PYTHON%"
    if defined APP_PYTHON goto launch
    echo ERROR: CIVICFORGE_PYTHON must point to a working Python 3.11-3.13 executable.
    goto failed
)
call :choose_python "%~dp0backend\.venv\Scripts\python.exe"
if defined APP_PYTHON goto launch
for %%V in (3.13 3.12 3.11) do (
    call :choose_python py -%%V
    if defined APP_PYTHON goto launch
)
for %%P in (python python3) do (
    call :choose_python %%P
    if defined APP_PYTHON goto launch
)
echo ERROR: Install Python 3.11-3.13, or set CIVICFORGE_PYTHON to its executable path.
goto failed

:launch
"%APP_PYTHON%" %APP_PYTHON_ARGS% "%~dp0scripts\start_windows.py" %*
set "APP_EXIT=%errorlevel%"
if not "%APP_EXIT%"=="0" pause
exit /b %APP_EXIT%

:choose_python
"%~1" %~2 -c "import sys; sys.exit(0 if (3, 11) <= sys.version_info[:2] < (3, 14) else 1)" >nul 2>&1
if errorlevel 1 exit /b
set "APP_PYTHON=%~1"
set "APP_PYTHON_ARGS=%~2"
exit /b

:failed
pause
exit /b 1
