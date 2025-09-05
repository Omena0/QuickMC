@echo off

rem QuickMC Windows Installation Script

echo Building QuickMC for Windows...

rem Build with Nuitka
python -m nuitka --standalone --windows-console-mode=force ^
    --product-name="QuickMC" --product-version=1.0.0 --file-description="The QuickMC launcher" ^
    --copyright="Copyright © 2025 Omena0. All rights reserved." ^
    --output-dir="..\__build" ^
    --include-package-data="minecraft_launcher_lib" ^
    --deployment --python-flag="-OO" --python-flag="-S" ^
    --assume-yes-for-downloads ^
    --lto=yes ^
    --jobs=16 ^
    --output-filename="QuickMC.exe" ^
    ..\src\main.py

rem Create directories
mkdir "%USERPROFILE%\QuickMC" 2>nul
mkdir "%USERPROFILE%\QuickMC\files" 2>nul
mkdir "%USERPROFILE%\QuickMC\data" 2>nul
mkdir "%USERPROFILE%\QuickMC\.minecraft" 2>nul

rem Copy files
xcopy "..\__build\main.dist\*" "%USERPROFILE%\QuickMC\files\" /E /I /Y

rem Copy config
copy "..\config.json" "%USERPROFILE%\QuickMC\data\"

rem Copy launcher
copy "launch.cmd" "%USERPROFILE%\QuickMC\"

rem Create Start Menu shortcut
powershell -Command "& { ^
    $WshShell = New-Object -comObject WScript.Shell; ^
    $Shortcut = $WshShell.CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\QuickMC.lnk'); ^
    $Shortcut.TargetPath = '%USERPROFILE%\QuickMC\launch.cmd'; ^
    $Shortcut.WorkingDirectory = '%USERPROFILE%\QuickMC'; ^
    $Shortcut.IconLocation = 'shell32.dll,21'; ^
    $Shortcut.Save() ^
}"

echo QuickMC installed successfully!
echo You can now find QuickMC in your Start Menu.
echo QuickMC will launch with console output for better debugging.
