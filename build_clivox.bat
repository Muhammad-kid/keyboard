@echo off
setlocal enableextensions enabledelayedexpansion

REM Change to the directory of this script
cd /d "%~dp0"

set "APP_NAME=Clivox"
set "MAIN=clivox.py"
set "DIST_DIR=dist"
set "BUILD_DIR=build"
set "SPEC_FILE=clivox.spec"

REM Detect Python launcher or python
set "PY=py -3"
%PY% -V >nul 2>&1 || set "PY=python"

if not exist "%MAIN%" (
  echo [ERROR] Cannot find %MAIN% in %cd%
  exit /b 1
)

REM Install/upgrade required build dependencies
echo [INFO] Ensuring pip, PyInstaller, and dependencies are installed...
%PY% -m pip install --upgrade pip >nul 2>&1
%PY% -m pip install --upgrade pyinstaller customtkinter pillow >nul 2>&1
if errorlevel 1 (
  echo [WARN] Some dependencies may have failed to install. Continuing...
)

REM Clean previous build outputs
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%SPEC_FILE%" del /f /q "%SPEC_FILE%"

REM Optional EXE icon if icon.ico exists
set "ICON_FLAG="
if exist "icon.ico" set "ICON_FLAG=--icon icon.ico"

echo [INFO] Building %APP_NAME%...
%PY% -m PyInstaller --noconfirm --onefile --windowed %ICON_FLAG% "%MAIN%"
if errorlevel 1 (
  echo [ERROR] PyInstaller build failed.
  exit /b 1
)

REM Copy runtime assets next to the exe
if not exist "%DIST_DIR%\tools" (
  if exist "tools" (
    echo [INFO] Copying tools/ folder next to the EXE...
    xcopy /e /i /y "tools" "%DIST_DIR%\tools" >nul
  ) else (
    echo [WARN] tools/ folder not found. Remember to place yt-dlp, ffmpeg, ffprobe in a tools folder next to the EXE.
  )
)

if exist "icon.png" (
  copy /y "icon.png" "%DIST_DIR%\" >nul
)

echo.
echo [SUCCESS] Build complete.
for %%F in ("%DIST_DIR%\*.exe") do echo EXE: %%~fF

echo.
echo Runtime layout expected:
echo   %%DIST_DIR%%\clivox.exe
echo   %%DIST_DIR%%\icon.png   [optional - used by Tk at runtime]
echo   %%DIST_DIR%%\tools\yt-dlp(.exe)
echo   %%DIST_DIR%%\tools\ffmpeg(.exe)
echo   %%DIST_DIR%%\tools\ffprobe(.exe)

echo.
pause