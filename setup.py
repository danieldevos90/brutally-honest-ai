"""
Setup script for Voice Insight Platform
"""

import asyncio
import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_environment():
    """Set up the development environment"""
    logger.info("Setting up Voice Insight Platform...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required")
        return False
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        logger.info("Creating .env file from template...")
        with open("env.example", "r") as template:
            with open(".env", "w") as env:
                env.write(template.read())
        logger.info("Please edit .env file with your configuration")
    
    # Install Python dependencies
    logger.info("Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        logger.info("Python dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False
    
    # Check for required system dependencies
    logger.info("Checking system dependencies...")
    required_commands = ["ffmpeg", "curl"]
    missing_commands = []
    
    for cmd in required_commands:
        try:
            subprocess.run([cmd, "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing_commands.append(cmd)
    
    if missing_commands:
        logger.warning(f"Missing system dependencies: {', '.join(missing_commands)}")
        logger.warning("Please install them using your system package manager")
    
    # Download Whisper model
    logger.info("Downloading Whisper model...")
    try:
        import whisper
        whisper.load_model("base")
        logger.info("Whisper model downloaded successfully")
    except Exception as e:
        logger.warning(f"Failed to download Whisper model: {e}")
    
    logger.info("Setup completed! Next steps:")
    logger.info("1. Edit .env file with your configuration")
    logger.info("2. Start databases: docker-compose up -d postgres qdrant ollama")
    logger.info("3. Pull LLM model: docker exec -it brutally-honest-ai-ollama-1 ollama pull mistral:7b")
    logger.info("4. Run the application: python main.py")
    
    return True

async def check_omi_connection():
    """Check OMI DevKit connection"""
    logger.info("Checking OMI DevKit connection...")
    
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        
        logger.info("Available serial ports:")
        for port in ports:
            logger.info(f"  {port.device}: {port.description}")
            if 'pico' in port.description.lower() or 'omi' in port.description.lower():
                logger.info(f"  -> Potential OMI device found: {port.device}")
        
        if not ports:
            logger.warning("No serial ports found. Make sure OMI DevKit is connected via USB-C")
        
    except ImportError:
        logger.error("pyserial not installed. Run: pip install pyserial")

async def test_components():
    """Test individual components"""
    logger.info("Testing components...")
    
    # Test database connections
    try:
        from src.database.manager import DatabaseManager
        db = DatabaseManager()
        if await db.initialize():
            logger.info("✓ Database connection successful")
            await db.cleanup()
        else:
            logger.error("✗ Database connection failed")
    except Exception as e:
        logger.error(f"✗ Database test failed: {e}")
    
    # Test LLM connection
    try:
        from src.llm.analyzer import LLMAnalyzer
        llm = LLMAnalyzer()
        if await llm.initialize():
            logger.info("✓ LLM connection successful")
            await llm.cleanup()
        else:
            logger.error("✗ LLM connection failed")
    except Exception as e:
        logger.error(f"✗ LLM test failed: {e}")
    
    # Test audio processor
    try:
        from src.audio.processor import AudioProcessor
        processor = AudioProcessor()
        if await processor.initialize():
            logger.info("✓ Audio processor initialized")
            await processor.cleanup()
        else:
            logger.error("✗ Audio processor failed")
    except Exception as e:
        logger.error(f"✗ Audio processor test failed: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Voice Insight Platform Setup")
    parser.add_argument("--setup", action="store_true", help="Set up the environment")
    parser.add_argument("--check-omi", action="store_true", help="Check OMI connection")
    parser.add_argument("--test", action="store_true", help="Test components")
    
    args = parser.parse_args()
    
    if args.setup:
        asyncio.run(setup_environment())
    elif args.check_omi:
        asyncio.run(check_omi_connection())
    elif args.test:
        asyncio.run(test_components())
    else:
        parser.print_help()
