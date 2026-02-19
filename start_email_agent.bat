@echo off
title Email to Email AI Agent
echo 🤖 EMAIL TO EMAIL AI AGENT
echo Automated Email Replies with AI
echo.

REM Check if Python is available
py -3 --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not available
    echo.
    echo 📥 INSTALLING PYTHON NOW...
    echo.
    
    REM Try to install Python via winget
    winget install Python.Python.3.11
    
    if errorlevel 1 (
        echo ⚠️  Winget installation failed. Opening Python download page...
        start https://www.python.org/downloads/
        echo.
        echo 📋 Please:
        echo 1. Download and install Python from the opened webpage
        echo 2. Make sure to check "Add Python to PATH" during installation  
        echo 3. Restart this script after installation
        pause
        exit /b 1
    ) else (
        echo ✅ Python installed! Please restart this script.
        pause
        exit /b 0
    )
)

echo ✅ Python is available
echo.

REM Create necessary directories
if not exist "logs" mkdir logs

REM Check if configuration exists
if exist "config.yaml" (
    echo 📋 Found configuration file
    echo 🚀 Starting Email Agent...
    echo.
    
    REM Check if dependencies are installed
    py -3 -c "import yaml" >nul 2>&1
    if errorlevel 1 (
        echo 📦 Installing required packages...
        py -3 -m pip install -r requirements.txt
        if errorlevel 1 (
            echo ❌ Failed to install packages. Check internet connection.
            pause
            exit /b 1
        )
    )
    
    echo 🤖 Launching Email to Email AI Agent...
    py -3 main_email_agent.py
    
) else (
    echo 🔧 No configuration found
    echo.
    echo 📋 Creating sample configuration...
    echo.
    
    REM Run main_email_agent.py to create sample config
    py -3 main_email_agent.py
    
    echo.
    echo 📧 Setup your Gmail App Password:
    echo 1. Go to Google Account Settings ^> Security
    echo 2. Enable 2-Factor Authentication
    echo 3. Create App Password for "Mail"
    echo 4. Update config.yaml with your email and app password
    echo.
    echo ✅ Then restart this script to begin monitoring emails
)

echo.
echo 🏁 Email Agent session ended
pause