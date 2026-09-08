@echo off
cd /d "%~dp0"
title Birthday Reminder Pro V7 - Build
echo.
echo Installing required packages...
py -3 -m pip install -U customtkinter pillow winotify pyinstaller
if errorlevel 1 (
  echo.
  echo Package installation failed.
  pause
  exit /b 1
)
echo.
echo Removing old build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "Birthday Reminder Pro.spec" del /q "Birthday Reminder Pro.spec"
echo.
echo Building EXE...
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name "Birthday Reminder Pro" Birthday_Reminder_Pro.py
if errorlevel 1 (
  echo.
  echo BUILD FAILED.
  pause
  exit /b 1
)
echo.
echo ==========================================
echo BUILD SUCCESSFUL
echo.
echo EXE:
echo %CD%\dist\Birthday Reminder Pro.exe
echo.
echo Run that EXE ONCE to install automatic
echo background notification at Windows login.
echo ==========================================
pause
