@echo off
title LitMus Application Compiler Layer
color 0A

echo.
echo  =======================================================
echo   LitMus Toolset Standalone Application Compilation Pipeline
echo  =======================================================
echo.

python --version >nul 2>&1
if errorlevel 1 ( echo Python compiler infrastructure not discovered. Build sequence terminated. & pause & exit /b 1 )

echo [1/4] Securing staging packaging dependencies...
python -m pip install pyinstaller PyPDF2 python-docx fpdf2 -q --quiet

echo [2/4] Wiping previous distribution workspaces...
if exist build       rmdir /s /q build
if exist dist        rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

echo [3/4] Packaging cross-compiled binary file structures (1-3 minutes expected)...
echo.

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "LitMus" ^
    --add-data "C:\Users\ayanp\Downloads\LitMus.png;." ^
    --hidden-import "PyPDF2" ^
    --hidden-import "docx" ^
    --hidden-import "fpdf" ^
    --hidden-import "tkinter" ^
    --hidden-import "tkinter.ttk" ^
    --hidden-import "tkinter.filedialog" ^
    --hidden-import "tkinter.scrolledtext" ^
    litmus.py

if errorlevel 1 (
    echo [FATAL ERROR] Compilation protocol failed under assembly exceptions.
    pause & exit /b 1
)

echo.
echo [4/4] COMPILATION ROUTINE EXECUTED SUCCESSFULLY!
echo.
echo  Distribution Executable Path: dist\LitMus.exe
echo  Deployment note: Host targets do not require python setups — simply run local Ollama tools.
echo.
explorer dist
pause