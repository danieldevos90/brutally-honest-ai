# 🎯 Brutally Honest AI - Complete System Guide

## Overview
This is the complete system that captures audio with a button toggle, streams it via USB/Bluetooth/WiFi to the local hub, and provides AI-powered transcription and brutal honest feedback.

## 🎙️ How Recording Works

### Button Toggle Recording
- **First Press**: Start recording
  - OLED shows "RECORDING"
  - LED pulses rapidly
  - Buzzer beeps once (high tone)
  - Sends "AUDIO_START" marker via USB
  
- **Second Press**: Stop recording
  - OLED shows "File saved"
  - LED returns to slow breathing
  - Buzzer beeps twice (descending tones)
  - Sends "AUDIO_END" marker via USB
  - File saved to SD card

## 🔌 Three Ways to Connect

### 1. USB Connection (Fastest, Real-time)
- **Auto-connects** when plugged in
- **Real-time audio streaming** during recording
- **Instant sync** with local hub
- **Status**: Green USB indicator in web interface

```
ESP32 ---USB---> Local Hub Server
                 (Real-time audio streaming)
```

### 2. Bluetooth LE (Wireless, Medium Speed)
- **Advertises as**: "BrutallyHonestAI"
- **Audio chunks** sent via BLE notifications
- **Status updates** via BLE characteristics
- **Range**: ~10 meters

```
ESP32 ---BLE---> Phone/Computer
                 (Wireless audio chunks)
```

### 3. WiFi AP Mode (File Download)
- **SSID**: "BrutallyHonestAI"
- **Password**: "brutal123"
- **Web interface**: http://192.168.4.1
- **Download recordings** as WAV files

```
ESP32 creates WiFi hotspot
Phone/Computer connects to download files
```

## 🖥️ Local Hub Features

### Real-time Processing
1. **Audio Reception**
   - Receives audio stream via USB
   - Buffers and saves as WAV file
   - Shows in web interface immediately

2. **AI Processing**
   - **Whisper**: Transcribes speech to text
   - **Language Model**: Provides brutal honest analysis
   - Results appear in web interface

### Web Interface (http://localhost:5555)
- **Connection Status**: Shows USB/WiFi/BLE status
- **Recording List**: All audio files with transcriptions
- **Audio Player**: Listen to recordings
- **AI Analysis**: See brutal feedback

## 📱 OLED Display Information

```
┌─────────────────┐
│ Brutally Honest AI│  <- Always shown
│                 │
│ RECORDING       │  <- Current status
│ Press to stop   │  <- Instructions
│                 │
│ Rec #5          │  <- Recording count
└─────────────────┘
```

## 🎨 LED Status Indicators

| Pattern | Meaning |
|---------|---------|
| Slow breathing | Idle, ready to record |
| Fast pulsing | Recording in progress |
| Triple flash | Success/File saved |
| Rapid flashing | Error |
| Off | No power/Not initialized |

## 🔊 Buzzer Feedback

| Sound | Meaning |
|-------|---------|
| Single high beep | Recording started |
| Two descending beeps | Recording stopped |
| Three ascending beeps | Device startup |
| Rapid beeps | Error/Warning |

## 🏃 Quick Start

### 1. Upload Firmware
```bash
# Put device in boot mode, then:
arduino-cli upload -p /dev/cu.usbmodem* --fqbn esp32:esp32:XIAO_ESP32S3:USBMode=hwcdc,CDCOnBoot=default esp32s3_complete.ino
```

### 2. Start Local Hub
```bash
cd local_hub
source venv/bin/activate
python hub_server_simple.py
```

### 3. Open Web Interface
Navigate to: http://localhost:5555

### 4. Start Recording
- Press button once to start
- Speak your message
- Press button again to stop
- Watch AI analysis appear!

## 🔧 Troubleshooting

### Device Not Detected
1. Check USB cable (must be data cable)
2. Ensure firmware has USB CDC enabled
3. Try different USB port

### No Audio
1. Check I2S microphone connections
2. Verify button is working (see count on OLED)
3. Monitor USB output for "AUDIO_START" marker

### BLE Not Connecting
1. Ensure BLE is enabled on phone/computer
2. Look for "BrutallyHonestAI" device
3. Check distance (within 10m)

### WiFi Issues
1. Connect to "BrutallyHonestAI" network
2. Password: "brutal123"
3. Navigate to 192.168.4.1

## 📊 Data Flow

```
1. Button Press
   ↓
2. Microphone captures audio (I2S)
   ↓
3. Audio streams via:
   - USB (real-time to hub)
   - BLE (chunks to app)
   - Saved to SD card
   ↓
4. Hub receives audio
   ↓
5. Whisper transcribes
   ↓
6. LLM analyzes
   ↓
7. Results in web interface
```

## 🎯 Complete Feature List

- ✅ Toggle recording (press to start/stop)
- ✅ USB audio streaming
- ✅ Bluetooth LE connectivity
- ✅ WiFi AP for file access
- ✅ SD card storage
- ✅ OLED status display
- ✅ LED animations
- ✅ Buzzer feedback
- ✅ Real-time transcription (Whisper)
- ✅ Brutally honest AI analysis
- ✅ Web interface for management
- ✅ Multi-connection support
- ✅ Auto-reconnect on USB
- ✅ Low power sleep modes
- ✅ OTA updates via WiFi

## 🚀 Next Steps

1. **Mobile App**: Create companion app for BLE
2. **Cloud Sync**: Optional cloud backup
3. **Voice Commands**: "Hey Brutal" activation
4. **Multi-language**: Support more languages
5. **Custom Models**: Train on specific feedback styles

---

**Your Brutally Honest AI device is now complete and ready to provide unfiltered feedback!** 🎉
