#!/usr/bin/env python3
"""
Brutally Honest AI - Unified Main Script
Uses the src/ structure with unified connector for both USB and BLE
"""

import asyncio
import logging
import sys
import json
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from audio.unified_connector import UnifiedESP32S3Connector, ConnectionType
from audio.omi_connector import RecordingInfo

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BrutallyHonestAI:
    """Main application class"""
    
    def __init__(self, preferred_connection: ConnectionType = ConnectionType.USB):
        self.connector = UnifiedESP32S3Connector(preferred_connection)
        self.running = False
        
    async def initialize(self) -> bool:
        """Initialize the system"""
        logger.info("🚀 Brutally Honest AI - Initializing...")
        
        if await self.connector.initialize():
            logger.info("✅ System initialized successfully")
            return True
        else:
            logger.error("❌ Failed to initialize system")
            return False
    
    async def get_system_status(self) -> dict:
        """Get comprehensive system status"""
        status = await self.connector.get_device_status()
        recordings = await self.connector.get_recordings()
        connection_info = self.connector.get_connection_info()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "device_status": status.__dict__ if status else None,
            "recordings": [
                {
                    "name": rec.name,
                    "size": rec.size,
                    "size_kb": round(rec.size / 1024, 1)
                } for rec in recordings
            ],
            "connection_info": connection_info,
            "total_recordings": len(recordings),
            "total_size_kb": round(sum(rec.size for rec in recordings) / 1024, 1)
        }
    
    async def interactive_mode(self):
        """Run interactive command mode"""
        print("\n🎯 Brutally Honest AI - Interactive Mode")
        print("=" * 50)
        
        while True:
            print("\n📋 Available Commands:")
            print("  1. Get System Status")
            print("  2. List Recordings")
            print("  3. Send Custom Command")
            print("  4. Get Connection Info")
            print("  5. Monitor Device (30s)")
            print("  6. Switch Connection Type")
            print("  7. Exit")
            
            try:
                choice = input("\n👉 Enter your choice (1-7): ").strip()
                
                if choice == '1':
                    await self._show_system_status()
                elif choice == '2':
                    await self._list_recordings()
                elif choice == '3':
                    await self._send_custom_command()
                elif choice == '4':
                    await self._show_connection_info()
                elif choice == '5':
                    await self._monitor_device()
                elif choice == '6':
                    await self._switch_connection()
                elif choice == '7':
                    break
                else:
                    print("❌ Invalid choice. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n⏹️ Interrupted by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    async def _show_system_status(self):
        """Show comprehensive system status"""
        print("\n📊 Getting system status...")
        status = await self.get_system_status()
        
        print("\n" + "=" * 50)
        print("📱 SYSTEM STATUS")
        print("=" * 50)
        print(f"⏰ Timestamp: {status['timestamp']}")
        
        if status['device_status']:
            ds = status['device_status']
            print(f"🔗 Connection: {ds['connection_type']}")
            print(f"📊 Recording: {'YES' if ds['recording'] else 'NO'}")
            print(f"📁 Files: {ds['files']}")
            print(f"💾 SD Card: {'Present' if ds['sd_card_present'] else 'Missing'}")
            print(f"📡 BLE: {'Connected' if ds['ble_connected'] else 'Disconnected'}")
            print(f"🧠 Free RAM: {ds['free_ram']} KB")
        
        print(f"📂 Total Recordings: {status['total_recordings']}")
        print(f"💽 Total Size: {status['total_size_kb']} KB")
        print("=" * 50)
    
    async def _list_recordings(self):
        """List all recordings"""
        print("\n📁 Getting recordings list...")
        recordings = await self.connector.get_recordings()
        
        if recordings:
            print(f"\n📂 Found {len(recordings)} recordings:")
            print("-" * 60)
            total_size = 0
            for i, rec in enumerate(recordings, 1):
                size_kb = rec.size / 1024
                total_size += rec.size
                print(f"{i:2d}. 📄 {rec.name}")
                print(f"     Size: {size_kb:.1f} KB ({rec.size:,} bytes)")
                if rec.date:
                    print(f"     Date: {rec.date}")
                print()
            
            print("-" * 60)
            print(f"📊 Total: {len(recordings)} files, {total_size / 1024:.1f} KB")
        else:
            print("📭 No recordings found")
    
    async def _send_custom_command(self):
        """Send custom command to device"""
        command = input("\n📤 Enter command to send (S/I/L): ").strip().upper()
        
        if command in ['S', 'I', 'L']:
            print(f"📡 Sending command '{command}'...")
            response = await self.connector.send_command(command)
            
            if response:
                print("\n📥 Device Response:")
                print("-" * 40)
                print(response)
                print("-" * 40)
            else:
                print("❌ No response from device")
        else:
            print("❌ Invalid command. Use S (status), I (info), or L (list files)")
    
    async def _show_connection_info(self):
        """Show connection information"""
        info = self.connector.get_connection_info()
        
        print("\n🔗 CONNECTION INFORMATION")
        print("=" * 40)
        print(json.dumps(info, indent=2, default=str))
        print("=" * 40)
    
    async def _monitor_device(self):
        """Monitor device for 30 seconds"""
        print("\n👂 Monitoring device for 30 seconds...")
        print("Press Ctrl+C to stop early")
        
        try:
            for i in range(30):
                status = await self.connector.get_device_status()
                if status:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] Recording: {status.recording}, Files: {status.files}, RAM: {status.free_ram}KB")
                
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️ Monitoring stopped by user")
    
    async def _switch_connection(self):
        """Switch connection type"""
        current = self.connector.current_connection
        print(f"\n🔄 Current connection: {current.value if current else 'None'}")
        print("Available connection types:")
        print("  1. USB (reliable)")
        print("  2. BLE (wireless)")
        
        choice = input("Enter choice (1-2): ").strip()
        
        if choice == '1':
            new_type = ConnectionType.USB
        elif choice == '2':
            new_type = ConnectionType.BLE
        else:
            print("❌ Invalid choice")
            return
        
        try:
            print(f"🔄 Switching to {new_type.value}...")
            await self.connector.disconnect()
            
            self.connector = UnifiedESP32S3Connector(preferred_connection=new_type)
            if await self.connector.initialize():
                print(f"✅ Switched to {new_type.value} connection")
            else:
                print(f"❌ Failed to switch to {new_type.value}")
                print("💡 Falling back to USB connection...")
                self.connector = UnifiedESP32S3Connector(preferred_connection=ConnectionType.USB)
                if await self.connector.initialize():
                    print("✅ Fallback to USB successful")
                else:
                    print("❌ All connections failed")
        except KeyboardInterrupt:
            print("\n⏹️ Connection switch interrupted")
            # Try to restore USB connection
            self.connector = UnifiedESP32S3Connector(preferred_connection=ConnectionType.USB)
            await self.connector.initialize()
        except Exception as e:
            print(f"❌ Connection switch error: {e}")
            # Try to restore USB connection
            self.connector = UnifiedESP32S3Connector(preferred_connection=ConnectionType.USB)
            await self.connector.initialize()
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up...")
        await self.connector.disconnect()

async def main():
    """Main entry point"""
    print("🎯 Brutally Honest AI - Unified System")
    print("=" * 60)
    
    # Parse command line arguments
    preferred_connection = ConnectionType.USB
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == 'ble':
            preferred_connection = ConnectionType.BLE
        elif sys.argv[1].lower() == 'usb':
            preferred_connection = ConnectionType.USB
    
    app = BrutallyHonestAI(preferred_connection)
    
    try:
        if await app.initialize():
            # Show initial status
            await app._show_system_status()
            
            # Run interactive mode
            await app.interactive_mode()
        else:
            print("❌ Failed to initialize system")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n⏹️ Shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await app.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
