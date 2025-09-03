#!/usr/bin/env python3
"""
Build Windows executable for Brutally Honest AI installer
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_requirements():
    """Install required packages"""
    print("📦 Installing build requirements...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller", "pillow"])

def create_icon():
    """Create an icon for the executable"""
    print("🎨 Creating application icon...")
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a 256x256 icon
        img = Image.new('RGB', (256, 256), color='#1a1a1a')
        draw = ImageDraw.Draw(img)
        
        # Draw "BH" text
        try:
            font = ImageFont.truetype("arial.ttf", 120)
        except:
            font = ImageFont.load_default()
            
        draw.text((50, 50), "BH", fill='#00ff88', font=font)
        
        # Draw subtitle
        try:
            small_font = ImageFont.truetype("arial.ttf", 30)
        except:
            small_font = ImageFont.load_default()
            
        draw.text((40, 180), "AI", fill='white', font=small_font)
        
        # Save as ICO
        img.save('brutally_honest.ico', format='ICO', sizes=[(16,16), (32,32), (48,48), (256,256)])
        print("✅ Icon created successfully")
        
    except Exception as e:
        print(f"⚠️  Could not create icon: {e}")
        print("Using default icon instead")

def build_executable():
    """Build the Windows executable using PyInstaller"""
    print("🔨 Building Windows executable...")
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "BrutallyHonestAI",
        "--onefile",
        "--windowed",
        "--icon", "brutally_honest.ico" if os.path.exists("brutally_honest.ico") else "NONE",
        "--add-data", "../omi_firmware;omi_firmware",
        "--add-data", "../frontend;frontend",
        "--add-data", "../installer;installer",
        "--add-data", "../bridge_server.py;.",
        "--add-data", "../INSTALLER_README.md;.",
        "--hidden-import", "tkinter",
        "--hidden-import", "serial",
        "--hidden-import", "serial.tools",
        "--hidden-import", "serial.tools.list_ports",
        "--hidden-import", "websockets",
        "--hidden-import", "requests",
        "installer_gui.py"
    ]
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("✅ Executable built successfully!")
        
        # Copy to dist folder
        if os.path.exists("dist/BrutallyHonestAI.exe"):
            print(f"📍 Executable location: {os.path.abspath('dist/BrutallyHonestAI.exe')}")
            print(f"📏 File size: {os.path.getsize('dist/BrutallyHonestAI.exe') / 1024 / 1024:.2f} MB")
    else:
        print("❌ Build failed!")
        sys.exit(1)

def create_installer():
    """Create NSIS installer if available"""
    print("\n📦 Creating Windows installer...")
    
    # Check if NSIS is installed
    nsis_path = None
    possible_paths = [
        r"C:\Program Files (x86)\NSIS\makensis.exe",
        r"C:\Program Files\NSIS\makensis.exe",
        "makensis.exe"  # If in PATH
    ]
    
    for path in possible_paths:
        if os.path.exists(path) or shutil.which(path):
            nsis_path = path
            break
    
    if nsis_path:
        print("✅ NSIS found, creating installer...")
        
        # Create required assets
        create_installer_assets()
        
        # Build installer
        result = subprocess.run([nsis_path, "windows_installer.nsi"])
        
        if result.returncode == 0:
            print("✅ Installer created successfully!")
            print(f"📍 Installer location: {os.path.abspath('BrutallyHonestAI-Setup.exe')}")
        else:
            print("❌ Installer creation failed!")
    else:
        print("⚠️  NSIS not found. Install from https://nsis.sourceforge.io/")
        print("The standalone executable is still available in the dist folder.")

def create_installer_assets():
    """Create bitmap images for NSIS installer"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create welcome bitmap (164x314)
        welcome = Image.new('RGB', (164, 314), color='#1a1a1a')
        draw = ImageDraw.Draw(welcome)
        draw.text((20, 50), "Brutally\nHonest\nAI", fill='#00ff88', font=ImageFont.load_default())
        welcome.save('welcome.bmp')
        
        # Create header bitmap (150x57)
        header = Image.new('RGB', (150, 57), color='#1a1a1a')
        draw = ImageDraw.Draw(header)
        draw.text((10, 20), "Brutally Honest AI", fill='#00ff88', font=ImageFont.load_default())
        header.save('header.bmp')
        
        # Create LICENSE.txt if not exists
        if not os.path.exists('LICENSE.txt'):
            with open('LICENSE.txt', 'w') as f:
                f.write("MIT License\n\nCopyright (c) 2024 Brutally Honest AI\n\n")
                f.write("Permission is hereby granted, free of charge...\n")
                
    except Exception as e:
        print(f"⚠️  Could not create installer assets: {e}")

def main():
    """Main build process"""
    print("🚀 Brutally Honest AI - Windows Build Script")
    print("=" * 50)
    
    # Change to installer directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Install requirements
    install_requirements()
    
    # Create icon
    create_icon()
    
    # Build executable
    build_executable()
    
    # Create installer
    create_installer()
    
    print("\n✅ Build complete!")
    print("\nNext steps:")
    print("1. Test the executable in the 'dist' folder")
    print("2. If NSIS is installed, use the installer")
    print("3. Distribute to users")

if __name__ == "__main__":
    main()
