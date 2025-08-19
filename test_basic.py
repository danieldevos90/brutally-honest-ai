#!/usr/bin/env python3
"""
Basic component testing for Voice Insight Platform
"""

import asyncio
import sys
import os
from pathlib import Path

def test_imports():
    """Test if all required packages can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import serial
        print("✅ pyserial imported")
    except ImportError as e:
        print(f"❌ pyserial import failed: {e}")
        return False
    
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        print(f"✅ Found {len(ports)} serial ports")
        for port in ports:
            print(f"   - {port.device}: {port.description}")
    except Exception as e:
        print(f"❌ Serial port enumeration failed: {e}")
    
    # Test other imports that don't require installation
    try:
        import asyncio
        import json
        import logging
        from datetime import datetime
        from dataclasses import dataclass
        from typing import List, Optional, Dict, Any
        print("✅ Standard library imports successful")
    except ImportError as e:
        print(f"❌ Standard library import failed: {e}")
        return False
    
    return True

def test_project_structure():
    """Test if project structure is correct"""
    print("\n📁 Testing project structure...")
    
    required_files = [
        "main.py",
        "requirements.txt",
        "docker-compose.yml",
        "src/audio/omi_connector.py",
        "src/audio/processor.py",
        "src/llm/analyzer.py",
        "src/database/manager.py",
        "src/models/schemas.py",
        "scripts/start_services.sh",
        "scripts/test_omi.py"
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
    
    return all_exist

def test_docker_availability():
    """Test if Docker is available"""
    print("\n🐳 Testing Docker availability...")
    
    try:
        import subprocess
        result = subprocess.run(["docker", "--version"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ Docker available: {result.stdout.strip()}")
            
            # Test docker-compose
            result = subprocess.run(["docker-compose", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ Docker Compose available: {result.stdout.strip()}")
                return True
            else:
                print("❌ Docker Compose not available")
                return False
        else:
            print("❌ Docker not available")
            return False
    except Exception as e:
        print(f"❌ Docker test failed: {e}")
        return False

def test_environment_file():
    """Test environment configuration"""
    print("\n⚙️ Testing environment configuration...")
    
    if Path(".env").exists():
        print("✅ .env file exists")
        
        # Check for required variables
        with open(".env", "r") as f:
            content = f.read()
            
        required_vars = [
            "POSTGRES_HOST",
            "POSTGRES_DB", 
            "QDRANT_HOST",
            "OLLAMA_URL",
            "LLM_MODEL"
        ]
        
        missing_vars = []
        for var in required_vars:
            if var not in content:
                missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️ Missing environment variables: {', '.join(missing_vars)}")
        else:
            print("✅ All required environment variables present")
            
        return len(missing_vars) == 0
    else:
        print("⚠️ .env file not found. Copy from env.example")
        return False

async def test_omi_connector():
    """Test OMI connector without actual hardware"""
    print("\n🎙️ Testing OMI connector (software only)...")
    
    try:
        # Import the connector
        sys.path.append(str(Path.cwd()))
        from src.audio.omi_connector import OMIDevKitConnector, AudioChunk
        
        print("✅ OMI connector imported successfully")
        
        # Test instantiation
        connector = OMIDevKitConnector()
        print("✅ OMI connector instantiated")
        
        # Test without actual hardware (will fail gracefully)
        result = await connector.initialize()
        if result:
            print("✅ OMI hardware connected!")
            await connector.cleanup()
        else:
            print("⚠️ No OMI hardware detected (expected if not connected)")
        
        return True
        
    except Exception as e:
        print(f"❌ OMI connector test failed: {e}")
        return False

def create_sample_env():
    """Create .env file from template if it doesn't exist"""
    if not Path(".env").exists() and Path("env.example").exists():
        print("📝 Creating .env file from template...")
        with open("env.example", "r") as src:
            with open(".env", "w") as dst:
                dst.write(src.read())
        print("✅ .env file created. Please edit with your configuration.")

async def main():
    """Run all basic tests"""
    print("🚀 Voice Insight Platform - Basic Testing\n")
    
    # Create .env if needed
    create_sample_env()
    
    tests = [
        ("Imports", test_imports),
        ("Project Structure", test_project_structure),
        ("Docker", test_docker_availability),
        ("Environment", test_environment_file),
    ]
    
    async_tests = [
        ("OMI Connector", test_omi_connector),
    ]
    
    results = []
    
    # Run synchronous tests
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} test crashed: {e}")
            results.append((name, False))
    
    # Run asynchronous tests
    for name, test_func in async_tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} test crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n📊 Test Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:<20} {status}")
        if result:
            passed += 1
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All basic tests passed!")
        print("\nNext steps:")
        print("1. Connect your OMI DevKit 2 via USB-C")
        print("2. Edit .env file with your configuration")
        print("3. Run: ./scripts/start_services.sh")
        print("4. Run: python main.py")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please fix issues before proceeding.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())
