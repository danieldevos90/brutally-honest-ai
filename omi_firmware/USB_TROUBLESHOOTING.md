# 🔧 ESP32S3 USB Troubleshooting Guide

## Why ESP32S3 Only Works in Boot Mode - Common Issues & Solutions

### 🚨 The Problem
When your ESP32S3 only appears as a USB device in boot mode but disappears after normal boot, it's usually due to:

1. **USB CDC not properly initialized in firmware**
2. **Incorrect USB mode settings during compilation**
3. **Firmware crash preventing USB initialization**
4. **Power issues causing brown-out reset**

## ✅ The Solution - USB Fixed Firmware

### Step 1: Upload the USB Fix Firmware

**Put device in BOOT mode:**
1. Disconnect USB cable
2. Hold BOOT button
3. Connect USB cable while holding BOOT
4. Release BOOT after 2 seconds

**Upload with proper settings:**
```bash
arduino-cli upload -p /dev/cu.usbmodem* --fqbn esp32:esp32:XIAO_ESP32S3:USBMode=hwcdc,CDCOnBoot=default esp32s3_usb_fixed.ino
```

### Step 2: Verify USB Operation

After upload completes:
1. **Disconnect** USB cable
2. **Wait 5 seconds**
3. **Reconnect** USB cable (without pressing any buttons)
4. Device should appear as `/dev/cu.usbmodem*`

### Step 3: Monitor Output

```bash
arduino-cli monitor -p /dev/cu.usbmodem* -c baudrate=115200
```

You should see:
```
=== ESP32S3 USB Fixed Firmware ===
✅ USB CDC initialized successfully!
✅ Device should now appear as USB serial port
🚀 Ready! Device is fully operational
💚 Heartbeat - USB working! Uptime: 5 seconds
```

## 🛠️ Critical Code Elements for USB

### 1. USB Initialization (MUST be first in setup())
```cpp
#include "USB.h"
#include "USBCDC.h"

USBCDC USBSerial;

void setup() {
    // CRITICAL: Initialize USB first!
    USB.begin();
    USBSerial.begin(115200);
    
    // Delay for USB enumeration
    delay(1000);
    
    // Now initialize other hardware...
}
```

### 2. Proper Build Flags
```bash
# Correct FQBN for Hardware CDC mode:
esp32:esp32:XIAO_ESP32S3:USBMode=hwcdc,CDCOnBoot=default

# NOT these (will cause issues):
# USBMode=cdc ❌
# USBMode=default ❌ (TinyUSB mode)
```

### 3. Avoid Common Pitfalls
```cpp
// ❌ DON'T DO THIS - Will crash before USB init
void setup() {
    Wire.begin();  // I2C before USB = bad
    SD.begin();    // SD before USB = bad
    
    USB.begin();   // Too late!
}

// ✅ DO THIS - USB first, then other hardware
void setup() {
    USB.begin();
    USBSerial.begin(115200);
    delay(1000);
    
    // Now safe to init other hardware
    Wire.begin();
    SD.begin();
}
```

## 🔍 Diagnostic Commands

### Check if device is visible:
```bash
# macOS
ls /dev/cu.* | grep usbmodem

# Linux
ls /dev/ttyACM*

# Windows
mode
```

### Check USB details:
```bash
# macOS - System Information
system_profiler SPUSBDataType | grep -A 10 "ESP32"

# Linux
lsusb -v | grep -A 10 "303a"
```

### Python check:
```python
import serial.tools.list_ports
for port in serial.tools.list_ports.comports():
    print(f"{port.device}: {port.description} (VID={port.vid:04X}, PID={port.pid:04X})")
```

## 🚦 LED Status Indicators

The USB Fix firmware provides visual feedback:

| LED Pattern | Meaning |
|-------------|---------|
| Breathing (slow fade) | USB working, device idle |
| 3x fade sequence on boot | USB initialization successful |
| Rapid flashing | Error state |
| Solid bright | Button pressed |

## 🆘 If USB Still Doesn't Work

### 1. Try Different USB Cable
Many USB-C cables are **charge-only**. Use a known good **data cable**.

### 2. Check Power Supply
Insufficient power can cause brown-out resets. Try:
- Different USB port
- Powered USB hub
- Shorter cable

### 3. Erase Flash Completely
```bash
# Put in boot mode, then:
esptool.py --chip esp32s3 --port /dev/cu.usbmodem* erase_flash
```

### 4. Update ESP32 Board Package
```bash
arduino-cli core update-index
arduino-cli core upgrade esp32:esp32
```

### 5. Test with Minimal Firmware
Upload `esp32s3_usb_fixed.ino` - it only initializes USB and basic hardware.

## 📝 Integration Checklist

When adding USB to your project:

- [ ] Include USB headers: `USB.h` and `USBCDC.h`
- [ ] Create global `USBCDC USBSerial`
- [ ] Call `USB.begin()` FIRST in setup()
- [ ] Call `USBSerial.begin(115200)` right after
- [ ] Add 1000ms delay for USB enumeration
- [ ] Use correct FQBN with `USBMode=hwcdc`
- [ ] Test button/LED to verify firmware is running
- [ ] Monitor heartbeat messages

## 🎯 Final Working Example

```cpp
#include "USB.h"
#include "USBCDC.h"

USBCDC USBSerial;

void setup() {
    // USB MUST be first!
    USB.begin();
    USBSerial.begin(115200);
    delay(1000);
    
    // Now your code...
    pinMode(LED_PIN, OUTPUT);
    USBSerial.println("Ready!");
}

void loop() {
    // Send heartbeat every 5 seconds
    static unsigned long last = 0;
    if (millis() - last > 5000) {
        last = millis();
        USBSerial.println("USB working!");
    }
}
```

## 🎉 Success Indicators

You know USB is working when:
1. Device appears in `/dev/cu.usbmodem*` after normal boot
2. Heartbeat messages appear every 5 seconds
3. LED shows breathing animation
4. Button press shows status in serial monitor
5. Device responds to 'T' command for hardware test

---

**Remember: USB initialization MUST happen before any other hardware initialization!**
