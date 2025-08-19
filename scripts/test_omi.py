#!/usr/bin/env python3
"""
Test script for OMI DevKit 2 connection
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.audio.omi_connector import OMIDevKitConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_omi_connection():
    """Test OMI DevKit connection"""
    logger.info("Testing OMI DevKit 2 connection...")
    
    connector = OMIDevKitConnector()
    
    try:
        # Initialize connection
        if await connector.initialize():
            logger.info("✅ OMI DevKit connected successfully!")
            
            # Get device info
            info = await connector.get_device_info()
            logger.info(f"Device info: {info}")
            
            # Test audio streaming for 5 seconds
            logger.info("Testing audio streaming for 5 seconds...")
            chunk_count = 0
            
            async def stream_test():
                nonlocal chunk_count
                async for chunk in connector.stream_audio():
                    chunk_count += 1
                    logger.info(f"Received audio chunk {chunk_count}: {len(chunk.data)} bytes")
                    
                    if chunk_count >= 10:  # Stop after 10 chunks
                        connector.stop_streaming()
                        break
            
            # Run streaming test with timeout
            try:
                await asyncio.wait_for(stream_test(), timeout=10.0)
                logger.info(f"✅ Audio streaming test completed. Received {chunk_count} chunks.")
            except asyncio.TimeoutError:
                logger.warning("⚠️ Audio streaming test timed out")
                connector.stop_streaming()
            
        else:
            logger.error("❌ Failed to connect to OMI DevKit")
            logger.info("Troubleshooting tips:")
            logger.info("1. Make sure OMI DevKit 2 is connected via USB-C")
            logger.info("2. Check if the device appears in system USB devices")
            logger.info("3. Ensure proper drivers are installed")
            logger.info("4. Try a different USB port or cable")
    
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
    
    finally:
        await connector.cleanup()

async def list_serial_ports():
    """List all available serial ports"""
    try:
        import serial.tools.list_ports
        
        ports = serial.tools.list_ports.comports()
        
        if ports:
            logger.info("Available serial ports:")
            for port in ports:
                vid = getattr(port, 'vid', 'N/A')
                pid = getattr(port, 'pid', 'N/A')
                logger.info(f"  {port.device}: {port.description} (VID: {vid}, PID: {pid})")
        else:
            logger.warning("No serial ports found")
            
    except ImportError:
        logger.error("pyserial not installed. Run: pip install pyserial")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test OMI DevKit 2 connection")
    parser.add_argument("--list-ports", action="store_true", help="List available serial ports")
    parser.add_argument("--test-connection", action="store_true", help="Test OMI connection")
    
    args = parser.parse_args()
    
    if args.list_ports:
        asyncio.run(list_serial_ports())
    elif args.test_connection:
        asyncio.run(test_omi_connection())
    else:
        # Run both by default
        asyncio.run(list_serial_ports())
        print()
        asyncio.run(test_omi_connection())
