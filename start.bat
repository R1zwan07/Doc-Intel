@echo off
chcp 65001 >nul
title DocIntel Launcher
color 0B

:: Get script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python from https://python.org
    pause
    exit /b 1
)

:: Run the launcher
python launcher.py
