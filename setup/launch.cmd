@echo off

rem QuickMC Launcher for Windows
rem This script launches QuickMC in a console window

cd /d "%~dp0"

echo QuickMC - Minecraft Launcher
echo ============================
echo.

rem Launch QuickMC
files\QuickMC.exe

echo.
echo Press any key to exit...
pause >nul
