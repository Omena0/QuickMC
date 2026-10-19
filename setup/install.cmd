@echo off

rem QuickMC Windows Installation Script

echo Building QuickMC for Windows...

rem Build with Nuitka
python -m nuitka --standalone --windows-console-mode=force ^
 --product-name="QuickMC" --product-version=1.0.0 --file-description="The QuickMC launcher" ^
 --copyright="Copyright © 2026 Omena0. All rights reserved." ^
 --output-dir="../__build" ^
 --include-package-data="minecraft_launcher_lib" ^
 --deployment --python-flag="-OO" --python-flag="-S" ^
 --assume-yes-for-downloads ^
 --lto=yes ^
 --pgo-c ^
 --pgo-python ^
 --target-arch=x86-64-v3 ^
 --jobs=16 ^
 --output-filename="QuickMC" ^
 --msvc=latest ^
 ../src/main.py

rem Create directories
mkdir "%USERPROFILE%\QuickMC" 2>nul
mkdir "%USERPROFILE%\QuickMC\files" 2>nul
mkdir "%USERPROFILE%\QuickMC\data" 2>nul
mkdir "%USERPROFILE%\QuickMC\.minecraft" 2>nul

rem Copy files
xcopy "..\__build\main.dist\*" "%USERPROFILE%\QuickMC\files\" /E /I /Y

rem Copy config only if it doesn't already exist
if not exist "%USERPROFILE%\QuickMC\data\config.json" (
    copy "..\config.json" "%USERPROFILE%\QuickMC\data\"
) else (
    echo Not overwriting existing config.json in %USERPROFILE%\QuickMC\data\
)

rem Copy launcher
copy "launch.cmd" "%USERPROFILE%\QuickMC\"

rem Create Start Menu shortcut
powershell -Command "& { ^
    $WshShell = New-Object -comObject WScript.Shell; ^
    $Shortcut = $WshShell.CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\QuickMC.lnk'); ^
    $Shortcut.TargetPath = '%USERPROFILE%\QuickMC\launch.cmd'; ^
    $Shortcut.WorkingDirectory = '%USERPROFILE%\QuickMC'; ^
    $Shortcut.IconLocation = 'shell32.dll,21'; ^
    $Shortcut.Save()^
}"

echo QuickMC installed successfully!
echo You can now find QuickMC in your Start Menu.
echo QuickMC will launch with console output for better debugging.
