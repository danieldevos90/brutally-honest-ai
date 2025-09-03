@echo off
REM Brutally Honest AI - Easy Installer for Windows
REM For XIAO ESP32S3 Sense + Expansion Board

setlocal enabledelayedexpansion

echo ============================================================
echo          BRUTALLY HONEST AI - EASY INSTALLER               
echo      For XIAO ESP32S3 Sense + Expansion Board             
echo ============================================================
echo.

REM Check for Python
echo Step 1: Checking dependencies...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation!
    pause
    exit /b 1
) else (
    echo [OK] Python found
)

REM Check for Arduino CLI
arduino-cli version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Arduino CLI not found. 
    echo Please download from: https://arduino.github.io/arduino-cli/latest/installation/
    echo Extract arduino-cli.exe to a folder in your PATH
    pause
    exit /b 1
) else (
    echo [OK] Arduino CLI found
)

REM Setup Arduino CLI
echo.
echo Step 2: Setting up Arduino CLI...
arduino-cli config init
arduino-cli config add board_manager.additional_urls https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
arduino-cli core update-index

REM Install ESP32 core
arduino-cli core list | findstr "esp32:esp32" >nul
if %errorlevel% neq 0 (
    echo Installing ESP32 core...
    arduino-cli core install esp32:esp32
) else (
    echo [OK] ESP32 core already installed
)

REM Install libraries
echo.
echo Step 3: Installing Arduino libraries...
arduino-cli lib install "U8g2"
arduino-cli lib install "ArduinoJson"

REM Setup Python environment
echo.
echo Step 4: Setting up Python environment...
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

echo Installing Python dependencies...
call venv\Scripts\activate.bat
pip install -r omi_firmware\requirements.txt

REM Detect device
echo.
echo Step 5: Looking for XIAO ESP32S3...
echo Please ensure your XIAO ESP32S3 is connected via USB-C cable
echo.
echo If device is not detected:
echo   1. Hold the BOOT button on the ESP32S3
echo   2. While holding BOOT, press and release RESET
echo   3. Keep holding BOOT for 2-3 seconds
echo   4. Release BOOT button
echo.

REM Get COM port from user
set /p DEVICE_PORT="Enter COM port (e.g., COM3): "

REM Choose firmware
echo.
echo Step 6: Choose firmware version:
echo   1) Full firmware (Recording, WiFi, BLE, Web interface)
echo   2) Simple toggle recording test (for testing)
echo   3) Basic OLED test (for troubleshooting)
set /p FIRMWARE_CHOICE="Select option (1-3): "

if "%FIRMWARE_CHOICE%"=="1" (
    set FIRMWARE_PATH=omi_firmware\esp32s3_ble\esp32s3_ble.ino
    echo Selected: Full firmware
) else if "%FIRMWARE_CHOICE%"=="2" (
    set FIRMWARE_PATH=omi_firmware\test_toggle_recording\test_toggle_recording.ino
    echo Selected: Toggle recording test
) else if "%FIRMWARE_CHOICE%"=="3" (
    set FIRMWARE_PATH=omi_firmware\test_oled_official\test_oled_official.ino
    echo Selected: OLED test
) else (
    echo Invalid selection
    pause
    exit /b 1
)

REM Compile firmware
echo.
echo Step 7: Compiling firmware...
arduino-cli compile --fqbn esp32:esp32:XIAO_ESP32S3 %FIRMWARE_PATH%
if %errorlevel% neq 0 (
    echo [ERROR] Compilation failed
    pause
    exit /b 1
)
echo [OK] Firmware compiled successfully

REM Upload firmware
echo.
echo Step 8: Uploading firmware to device...
echo Note: If upload fails, put device in BOOT mode (see Step 5)
arduino-cli upload --fqbn esp32:esp32:XIAO_ESP32S3 --port %DEVICE_PORT% %FIRMWARE_PATH%
if %errorlevel% neq 0 (
    echo [ERROR] Upload failed. Try putting device in BOOT mode.
    pause
    exit /b 1
)
echo [OK] Firmware uploaded successfully!

REM Start services (if full firmware)
if "%FIRMWARE_CHOICE%"=="1" (
    echo.
    echo Step 9: Starting services...
    
    echo Starting Whisper transcription service...
    start cmd /k "cd omi_firmware && ..\venv\Scripts\python esp32s3_companion.py"
    
    echo Starting web interface...
    cd frontend
    if exist "node_modules" (
        start cmd /k "npm start"
    ) else (
        echo Installing Node.js dependencies...
        call npm install
        start cmd /k "npm start"
    )
    cd ..
)

REM Success message
echo.
echo ============================================================
echo                 INSTALLATION COMPLETE!
echo ============================================================
echo.
echo Your Brutally Honest AI device is ready!
echo.
echo How to use:
echo   - The OLED display should show 'Brutal Honest Query'
echo   - Press the button once to START recording
echo   - Press again to STOP recording
echo   - LED blinks while recording
echo   - Recordings are saved to SD card

if "%FIRMWARE_CHOICE%"=="1" (
    echo.
    echo Access points:
    echo   - WiFi AP: SSID='OMI-ESP32S3', Password='brutalhonest'
    echo   - Web interface: http://localhost:3000
    echo   - Device web server: http://192.168.4.1 (when connected to AP)
)

echo.
echo Troubleshooting:
echo   - If display doesn't work: Run this script again and choose option 3
echo   - If button doesn't respond: Check you're pressing the user button (D1)
echo   - For logs: arduino-cli monitor --port %DEVICE_PORT%
echo.
echo Enjoy your Brutally Honest AI device!
echo.
pause
