; Brutally Honest AI NSIS Installer Script
; Creates a professional Windows installer

!include "MUI2.nsh"
!include "FileFunc.nsh"

; General Configuration
Name "Brutally Honest AI"
OutFile "BrutallyHonestAI-Setup.exe"
InstallDir "$PROGRAMFILES\BrutallyHonestAI"
InstallDirRegKey HKLM "Software\BrutallyHonestAI" "Install_Dir"
RequestExecutionLevel admin

; Version Info
VIProductVersion "1.0.0.0"
VIAddVersionKey "ProductName" "Brutally Honest AI"
VIAddVersionKey "ProductVersion" "1.0"
VIAddVersionKey "CompanyName" "Brutally Honest AI Team"
VIAddVersionKey "LegalCopyright" "© 2024 Brutally Honest AI"
VIAddVersionKey "FileDescription" "AI-powered voice recorder for XIAO ESP32S3"
VIAddVersionKey "FileVersion" "1.0"

; UI Configuration
!define MUI_ICON "installer_icon.ico"
!define MUI_UNICON "uninstaller_icon.ico"
!define MUI_BGCOLOR "1a1a1a"
!define MUI_TEXTCOLOR "FFFFFF"
!define MUI_WELCOMEFINISHPAGE_BITMAP "welcome.bmp"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "header.bmp"
!define MUI_HEADERIMAGE_RIGHT

; Welcome Page
!define MUI_WELCOMEPAGE_TITLE "Welcome to Brutally Honest AI Setup"
!define MUI_WELCOMEPAGE_TEXT "This wizard will guide you through the installation of Brutally Honest AI.$\r$\n$\r$\nTransform your XIAO ESP32S3 Sense into an AI-powered voice recorder with:$\r$\n  • Voice recording with button toggle$\r$\n  • OLED display showing 'Brutal Honest Query'$\r$\n  • Automatic Whisper AI transcription$\r$\n  • WiFi & Bluetooth connectivity$\r$\n  • Web interface for management$\r$\n$\r$\nClick Next to continue."

; License Page (optional)
!define MUI_LICENSEPAGE_TEXT_TOP "Please review the license terms before installing."
!define MUI_LICENSEPAGE_TEXT_BOTTOM "Click I Agree to continue."

; Directory Page
!define MUI_DIRECTORYPAGE_TEXT_TOP "Choose the folder where you want to install Brutally Honest AI."

; Components Page
!define MUI_COMPONENTSPAGE_TEXT_TOP "Select the components you want to install."

; Install Page
!define MUI_INSTFILESPAGE_COLORS "FFFFFF 000000"

; Finish Page
!define MUI_FINISHPAGE_TITLE "Installation Complete"
!define MUI_FINISHPAGE_TEXT "Brutally Honest AI has been installed on your computer.$\r$\n$\r$\nClick Finish to close Setup."
!define MUI_FINISHPAGE_RUN "$INSTDIR\BrutallyHonestAI.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Launch Brutally Honest AI Installer"
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\README.txt"
!define MUI_FINISHPAGE_SHOWREADME_TEXT "View README"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Languages
!insertmacro MUI_LANGUAGE "English"

; Components
Section "Core Files (required)" SEC_CORE
  SectionIn RO
  
  SetOutPath "$INSTDIR"
  
  ; Core Python files
  File /r "..\installer\*.*"
  File /r "..\omi_firmware\*.*"
  File /r "..\frontend\*.*"
  File "..\bridge_server.py"
  File "..\install_brutally_honest.bat"
  File "..\INSTALLER_README.md"
  
  ; Create launcher executable
  FileOpen $0 "$INSTDIR\BrutallyHonestAI.exe" w
  FileWrite $0 '@echo off$\r$\n'
  FileWrite $0 'cd /d "%~dp0"$\r$\n'
  FileWrite $0 'if not exist "venv" ($\r$\n'
  FileWrite $0 '  echo Creating Python virtual environment...$\r$\n'
  FileWrite $0 '  python -m venv venv$\r$\n'
  FileWrite $0 ')$\r$\n'
  FileWrite $0 'venv\Scripts\python.exe installer\installer_gui.py$\r$\n'
  FileClose $0
  
  ; Write registry keys
  WriteRegStr HKLM SOFTWARE\BrutallyHonestAI "Install_Dir" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BrutallyHonestAI" "DisplayName" "Brutally Honest AI"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BrutallyHonestAI" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BrutallyHonestAI" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BrutallyHonestAI" "NoRepair" 1
  WriteUninstaller "$INSTDIR\uninstall.exe"
  
SectionEnd

Section "Start Menu Shortcuts" SEC_SHORTCUTS
  CreateDirectory "$SMPROGRAMS\Brutally Honest AI"
  CreateShortcut "$SMPROGRAMS\Brutally Honest AI\Brutally Honest AI.lnk" "$INSTDIR\BrutallyHonestAI.exe" "" "$INSTDIR\BrutallyHonestAI.exe" 0
  CreateShortcut "$SMPROGRAMS\Brutally Honest AI\README.lnk" "$INSTDIR\README.txt"
  CreateShortcut "$SMPROGRAMS\Brutally Honest AI\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
SectionEnd

Section "Desktop Shortcut" SEC_DESKTOP
  CreateShortcut "$DESKTOP\Brutally Honest AI.lnk" "$INSTDIR\BrutallyHonestAI.exe" "" "$INSTDIR\BrutallyHonestAI.exe" 0
SectionEnd

Section "USB Drivers" SEC_DRIVERS
  ; Download and install USB drivers
  DetailPrint "Installing USB drivers for ESP32..."
  
  ; CP210x drivers
  NSISdl::download "https://www.silabs.com/documents/public/software/CP210x_Universal_Windows_Driver.zip" "$TEMP\cp210x.zip"
  Pop $0
  StrCmp $0 "success" +2
    DetailPrint "Failed to download CP210x drivers"
  
  ; CH340 drivers  
  NSISdl::download "http://www.wch-ic.com/downloads/CH341SER_ZIP.html" "$TEMP\ch340.zip"
  Pop $0
  StrCmp $0 "success" +2
    DetailPrint "Failed to download CH340 drivers"
    
  DetailPrint "Please install USB drivers manually if needed"
SectionEnd

; Descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_CORE} "Core application files (required)"
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_SHORTCUTS} "Create Start Menu shortcuts"
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_DESKTOP} "Create Desktop shortcut"
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_DRIVERS} "USB drivers for ESP32 boards"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; Check Prerequisites
Function .onInit
  ; Check for Python
  nsExec::ExecToStack 'python --version'
  Pop $0
  Pop $1
  StrCmp $0 0 +3
    MessageBox MB_YESNO|MB_ICONEXCLAMATION "Python 3 is required but not found. Would you like to download it?" IDYES download_python
    Abort
  
  download_python:
    ExecShell "open" "https://www.python.org/downloads/"
    
  ; Check for Arduino CLI
  nsExec::ExecToStack 'arduino-cli version'
  Pop $0
  StrCmp $0 0 +2
    DetailPrint "Arduino CLI will be installed during setup"
FunctionEnd

; Uninstaller
Section "Uninstall"
  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BrutallyHonestAI"
  DeleteRegKey HKLM SOFTWARE\BrutallyHonestAI

  ; Remove files
  RMDir /r "$INSTDIR"

  ; Remove shortcuts
  Delete "$SMPROGRAMS\Brutally Honest AI\*.*"
  RMDir "$SMPROGRAMS\Brutally Honest AI"
  Delete "$DESKTOP\Brutally Honest AI.lnk"
SectionEnd
