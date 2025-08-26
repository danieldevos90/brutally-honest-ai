/*
 * ESP32S3 Sense - Working PDM Microphone with USB Sync
 * Fixed version using ESP32-I2S library
 */

#include <ESP_I2S.h>
#include <Wire.h>
#include <U8g2lib.h>
#include <SD.h>
#include <SPI.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLE2902.h>

// USB Serial
#define USBSerial Serial

// Expansion Board Pins (from documentation)
#define BUTTON_PIN 2        // D1 on expansion board
#define BUZZER_PIN 3        // A3 on expansion board  
#define LED_PIN 0           // D0 on expansion board
#define SD_CS_PIN 21        // SD card chip select
#define OLED_SDA 5          // I2C SDA (Pin 5 on XIAO Expansion Board)
#define OLED_SCL 4          // I2C SCL (Pin 4 on XIAO Expansion Board)

// PDM Microphone pins for ESP32S3 Sense
#define PDM_CLK_PIN 42
#define PDM_DATA_PIN 41

// Audio configuration
#define SAMPLE_RATE 16000
#define SAMPLE_BITS 16

// I2S instance
I2SClass I2S;

// OLED Display
// OLED Display - Use U8X8 library like in Seeed documentation
U8X8_SSD1306_128X64_NONAME_HW_I2C u8x8(/* reset=*/ U8X8_PIN_NONE);

// Recording state
volatile bool isRecording = false;
volatile bool buttonPressed = false;
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 50;
int recordingCount = 0;

// OLED status
bool oledAvailable = false;

// Audio buffer
int16_t audioBuffer[512];

// BLE UUIDs
#define SERVICE_UUID        "12345678-1234-5678-1234-56789abcdef0"
#define AUDIO_CHAR_UUID     "12345678-1234-5678-1234-56789abcdef1"
#define STATUS_CHAR_UUID    "12345678-1234-5678-1234-56789abcdef2"

BLECharacteristic *pAudioCharacteristic;
BLECharacteristic *pStatusCharacteristic;
bool deviceConnected = false;

// SD Card
bool sdCardPresent = false;
File currentFile;

// LED animation
int ledBrightness = 0;
int ledDirection = 1;
unsigned long lastLedUpdate = 0;

void IRAM_ATTR handleButtonPress() {
    unsigned long currentTime = millis();
    if (currentTime - lastDebounceTime > debounceDelay) {
        buttonPressed = true;
        lastDebounceTime = currentTime;
    }
}

class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
        deviceConnected = true;
        USBSerial.println("📱 BLE Client Connected!");
    }

    void onDisconnect(BLEServer* pServer) {
        deviceConnected = false;
        USBSerial.println("📱 BLE Client Disconnected!");
    }
};

void setup() {
    // Initialize USB Serial
    USBSerial.begin(115200);
    delay(2000);
    
    USBSerial.println("🚀 ESP32S3 Sense PDM Audio Recorder Starting...");
    
    // Initialize OLED display with improved I2C handling
    USBSerial.println("🔄 Initializing OLED display...");
    
    // Initialize I2C with proper error handling
    Wire.end();  // End any previous I2C session
    delay(50);
    
    USBSerial.printf("🔧 Starting I2C on SDA=%d, SCL=%d\n", OLED_SDA, OLED_SCL);
    
    // Try multiple I2C configurations
    USBSerial.println("🔄 Trying different I2C configurations...");
    
    // Configuration 1: SDA=5, SCL=4 (current)
    USBSerial.println("Config 1: SDA=5, SCL=4");
    Wire.end();
    Wire.begin(5, 4);
    Wire.setClock(100000);
    delay(100);
    
    // Quick test
    Wire.beginTransmission(0x51); // RTC address
    uint8_t rtc_test1 = Wire.endTransmission();
    USBSerial.printf("  RTC test (0x51): %s\n", rtc_test1 == 0 ? "OK" : "NACK");
    
    // Configuration 2: Try default pins
    USBSerial.println("Config 2: Default I2C pins");
    Wire.end();
    Wire.begin(); // Use default pins
    Wire.setClock(100000);
    delay(100);
    
    Wire.beginTransmission(0x51);
    uint8_t rtc_test2 = Wire.endTransmission();
    USBSerial.printf("  RTC test (0x51): %s\n", rtc_test2 == 0 ? "OK" : "NACK");
    
    // Configuration 3: Try SDA=4, SCL=5 (original wrong config)
    USBSerial.println("Config 3: SDA=4, SCL=5 (testing old config)");
    Wire.end();
    Wire.begin(4, 5);
    Wire.setClock(100000);
    delay(100);
    
    Wire.beginTransmission(0x51);
    uint8_t rtc_test3 = Wire.endTransmission();
    USBSerial.printf("  RTC test (0x51): %s\n", rtc_test3 == 0 ? "OK" : "NACK");
    
    // Go back to correct configuration
    USBSerial.println("🔄 Returning to SDA=5, SCL=4 configuration");
    Wire.end();
    Wire.begin(OLED_SDA, OLED_SCL);
    Wire.setClock(100000);
    delay(100);
    
    // Comprehensive I2C scan for debugging
    bool oledFound = false;
    USBSerial.println("🔍 Comprehensive I2C scan starting...");
    USBSerial.println("     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f");
    
    int devicesFound = 0;
    USBSerial.println("Scanning ALL I2C addresses (0x00-0x7F):");
    for (int address = 1; address < 127; address++) {  // Skip 0x00 and 0x7F (reserved)
        if (address % 16 == 0) {
            USBSerial.printf("%02x: ", address);
        }
        
        Wire.beginTransmission(address);
        uint8_t error = Wire.endTransmission();
        
        if (error == 0) {
            USBSerial.printf("%02x ", address);
            devicesFound++;
            
            // Identify common I2C devices
            if (address == 0x3C || address == 0x3D) {
                USBSerial.printf("← OLED-SSD1306! ");
                oledFound = true;
            } else if (address == 0x78 >> 1 || address == 0x7A >> 1) {
                USBSerial.printf("← OLED-SH1106! ");
                oledFound = true;
            } else if (address == 0x51) {
                USBSerial.printf("← RTC-PCF8563! ");
            } else if (address >= 0x48 && address <= 0x4F) {
                USBSerial.printf("← Sensor! ");
            } else {
                USBSerial.printf("← Unknown! ");
            }
        } else {
            USBSerial.print("-- ");
        }
        
        if ((address + 1) % 16 == 0) {
            USBSerial.println();
        }
        delay(2);
    }
    
    USBSerial.println();
    USBSerial.printf("🎯 I2C scan complete! Found %d device(s)\n", devicesFound);
    
    if (devicesFound == 0) {
        USBSerial.println("❌ No I2C devices found!");
        USBSerial.println("💡 Wiring check:");
        USBSerial.println("   - SDA (Pin 5) connected?");
        USBSerial.println("   - SCL (Pin 4) connected?");
        USBSerial.println("   - VCC to 3.3V?");
        USBSerial.println("   - GND connected?");
    }
    
    if (!oledFound) {
        USBSerial.println("❌ OLED display not detected - continuing without display");
        oledAvailable = false;
    } else {
        // Initialize OLED using U8X8 following Seeed documentation
        u8x8.begin();
        u8x8.setFlipMode(1); // As shown in Seeed documentation
        
        // Test display
        u8x8.setFont(u8x8_font_chroma48medium8_r);
        u8x8.setCursor(0, 0);
        u8x8.print("Brutal Honest");
        u8x8.setCursor(0, 2);
        u8x8.print("Query System");
        u8x8.setCursor(0, 4);
        u8x8.print("Ready!");
        
        oledAvailable = true;
        USBSerial.println("✅ OLED initialized with U8X8!");
        
        // Brief test animation
        delay(1000);
        u8x8.clear();
        u8x8.setCursor(0, 2);
        u8x8.print("Display OK!");
        delay(1000);
    }
    
    // Initialize pins
    pinMode(BUTTON_PIN, INPUT_PULLUP);
    pinMode(LED_PIN, OUTPUT);
    pinMode(BUZZER_PIN, OUTPUT);
    
    // Attach interrupt for button
    attachInterrupt(digitalPinToInterrupt(BUTTON_PIN), handleButtonPress, FALLING);
    
    // Initialize LED PWM
    ledcAttach(LED_PIN, 5000, 8); // 5kHz, 8-bit resolution
    
    // Initialize SD card
    if (SD.begin(SD_CS_PIN)) {
        sdCardPresent = true;
        USBSerial.println("✅ SD card initialized");
    } else {
        USBSerial.println("❌ SD card initialization failed");
    }
    
    // Initialize PDM microphone using ESP32-I2S library
    I2S.setPins(-1, PDM_CLK_PIN, PDM_DATA_PIN, -1, -1);
    
    // For PDM mode: I2S_MODE_PDM_RX, sample rate, data width, channel format
    if (I2S.begin(I2S_MODE_PDM_RX, SAMPLE_RATE, I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_MONO)) {
        USBSerial.println("✅ PDM Microphone initialized!");
    } else {
        USBSerial.println("❌ Failed to initialize PDM microphone!");
    }
    
    // Initialize BLE
    initBLE();
    
    // Success beep
    tone(BUZZER_PIN, 1000, 100);
    delay(100);
    tone(BUZZER_PIN, 1500, 100);
    
    USBSerial.println("🎙️ Ready! Press button to toggle recording.");
    updateDisplay();
}

void initBLE() {
    BLEDevice::init("ESP32S3-Audio");
    BLEServer *pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());
    
    BLEService *pService = pServer->createService(SERVICE_UUID);
    
    // Audio characteristic for streaming
    pAudioCharacteristic = pService->createCharacteristic(
        AUDIO_CHAR_UUID,
        BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
    );
    pAudioCharacteristic->addDescriptor(new BLE2902());
    
    // Status characteristic
    pStatusCharacteristic = pService->createCharacteristic(
        STATUS_CHAR_UUID,
        BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
    );
    pStatusCharacteristic->addDescriptor(new BLE2902());
    
    pService->start();
    BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->setScanResponse(true);
    pAdvertising->setMinPreferred(0x06);
    pAdvertising->setMinPreferred(0x12);
    BLEDevice::startAdvertising();
    
    USBSerial.println("✅ BLE Service started");
}

void startRecording() {
    isRecording = true;
    USBSerial.println("🎤 Recording started!");
    USBSerial.println("AUDIO_START"); // Marker for USB streaming
    USBSerial.flush(); // Ensure marker is sent before audio data
    
    // Feedback
    tone(BUZZER_PIN, 2000, 100);
    
    // Start LED animation
    ledBrightness = 0;
    ledDirection = 1;
}

void stopRecording() {
    isRecording = false;
    
    USBSerial.flush(); // Flush any remaining audio data
    USBSerial.println("AUDIO_END"); // Marker for USB streaming
    USBSerial.println("⏹️ Recording stopped!");
    
    recordingCount++;
    
    // Feedback
    tone(BUZZER_PIN, 1000, 100);
    delay(100);
    tone(BUZZER_PIN, 500, 100);
    
    // Turn off LED
    ledcWrite(LED_PIN, 0);
}

void updateDisplay() {
    // Avoid display updates too frequently
    static unsigned long lastDisplayUpdate = 0;
    if (millis() - lastDisplayUpdate < 500) return;
    lastDisplayUpdate = millis();
    
    // Add periodic I2C debug info
    static unsigned long lastI2CDebug = 0;
    if (millis() - lastI2CDebug > 10000) { // Every 10 seconds
        lastI2CDebug = millis();
        USBSerial.println("🔍 Periodic I2C status check:");
        USBSerial.printf("   OLED Available: %s\n", oledAvailable ? "YES" : "NO");
        USBSerial.printf("   I2C SDA Pin: %d, SCL Pin: %d\n", OLED_SDA, OLED_SCL);
        
        // Quick OLED address check
        Wire.beginTransmission(0x3C);
        uint8_t error3C = Wire.endTransmission();
        Wire.beginTransmission(0x3D);
        uint8_t error3D = Wire.endTransmission();
        USBSerial.printf("   0x3C response: %s, 0x3D response: %s\n", 
                       error3C == 0 ? "OK" : "NACK", 
                       error3D == 0 ? "OK" : "NACK");
    }
    
    // If OLED is not available, print status to serial instead
    if (!oledAvailable) {
        USBSerial.printf("📱 Status: %s | Files: %d | BLE: %s\n",
                         isRecording ? "RECORDING" : "Ready",
                         recordingCount,
                         deviceConnected ? "Connected" : "Disconnected");
        return;
    }
    
    // Clear display and set font
    u8x8.clear();
    u8x8.setFont(u8x8_font_chroma48medium8_r);
    
    // Title
    u8x8.setCursor(0, 0);
    u8x8.print("Brutal Honest");
    u8x8.setCursor(0, 1);
    u8x8.print("Query");
    
    // Status
    u8x8.setCursor(0, 3);
    if (isRecording) {
        u8x8.print("RECORDING...");
        u8x8.setCursor(0, 4);
        u8x8.print("Press to stop");
    } else {
        u8x8.print("Ready");
        u8x8.setCursor(0, 4);
        u8x8.print("Press to rec");
    }
    
    // Recording count
    u8x8.setCursor(0, 6);
    u8x8.print("Files: ");
    u8x8.setCursor(7, 6);
    u8x8.print(recordingCount);
    
    // BLE status
    u8x8.setCursor(0, 7);
    if (deviceConnected) {
        u8x8.print("BLE: ON");
    } else {
        u8x8.print("BLE: OFF");
    }
}

void updateLED() {
    if (isRecording) {
        // Smooth breathing effect
        unsigned long currentTime = millis();
        if (currentTime - lastLedUpdate > 10) {
            ledBrightness += ledDirection * 5;
            if (ledBrightness >= 255) {
                ledBrightness = 255;
                ledDirection = -1;
            } else if (ledBrightness <= 0) {
                ledBrightness = 0;
                ledDirection = 1;
            }
            ledcWrite(LED_PIN, ledBrightness);
            lastLedUpdate = currentTime;
        }
    }
}

void handleRecording() {
    if (!isRecording) return;
    
    // Read audio data sample by sample
    int samplesRead = 0;
    int16_t pcmBuffer[512];  // Buffer for processed PCM data
    
    while (I2S.available() && samplesRead < 512) {
        int32_t sample = I2S.read();
        // PDM to PCM conversion with gain adjustment
        // Shift right by 14 bits to convert from 32-bit PDM to 16-bit PCM range
        pcmBuffer[samplesRead] = (int16_t)(sample >> 14);
        samplesRead++;
    }
    
    if (samplesRead > 0) {
        int bytesRead = samplesRead * 2; // 16-bit samples
        
        // Send processed PCM audio via USB for real-time streaming
        USBSerial.write((uint8_t*)pcmBuffer, bytesRead);
        
        // Calculate and show audio level for debugging
        int32_t sum = 0;
        for (int i = 0; i < samplesRead; i++) {
            sum += abs(pcmBuffer[i]);
        }
        int32_t avgLevel = sum / samplesRead;
        
        // Print audio level periodically
        static int printCounter = 0;
        if (++printCounter % 100 == 0) {  // Every 100 reads
            USBSerial.printf("🎤 Audio level: %d (samples: %d)\n", avgLevel, samplesRead);
        }
        
        // Copy to audioBuffer for BLE
        memcpy(audioBuffer, pcmBuffer, bytesRead);
        
        // Send via BLE if connected
        if (deviceConnected && pAudioCharacteristic) {
            // BLE has 20-byte limit per packet, so we need to chunk
            for (int i = 0; i < bytesRead; i += 20) {
                int chunkSize = min(20, bytesRead - i);
                pAudioCharacteristic->setValue((uint8_t*)audioBuffer + i, chunkSize);
                pAudioCharacteristic->notify();
            }
        }
    }
}

void sendStatus() {
    if (deviceConnected && pStatusCharacteristic) {
        char status[64];
        sprintf(status, "Recording: %s, Files: %d", 
                isRecording ? "YES" : "NO", 
                recordingCount);
        pStatusCharacteristic->setValue(status);
        pStatusCharacteristic->notify();
    }
    
    // Also send via USB
    USBSerial.printf("💚 Status - Recording: %s, BLE: %s, Files: %d\n",
                     isRecording ? "YES" : "NO",
                     deviceConnected ? "Connected" : "Disconnected",
                     recordingCount);
}

void loop() {
    // Handle button press
    if (buttonPressed) {
        buttonPressed = false;
        
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
        
        updateDisplay();
        sendStatus();
    }
    
    // Handle recording
    handleRecording();
    
    // Update LED animation
    updateLED();
    
    // Send periodic status updates
    static unsigned long lastStatusUpdate = 0;
    if (millis() - lastStatusUpdate > 5000) {
        sendStatus();
        lastStatusUpdate = millis();
    }
    
    // Check for serial commands
    if (USBSerial.available()) {
        String command = USBSerial.readString();
        command.trim();
        
        if (command == "scan" || command == "i2c") {
            USBSerial.println("\n🔍 Manual I2C scan requested:");
            performI2CScan();
        } else if (command == "test") {
            USBSerial.println("\n🔧 Manual I2C configuration test:");
            testI2CConfigurations();
        } else if (command == "help") {
            USBSerial.println("\n📋 Available commands:");
            USBSerial.println("  scan/i2c - Perform I2C device scan");
            USBSerial.println("  test     - Test different I2C configurations");
            USBSerial.println("  help     - Show this help");
        }
    }
}

// Function to perform I2C scan
void performI2CScan() {
    USBSerial.println("     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f");
    
    int devicesFound = 0;
    for (int address = 1; address < 127; address++) {
        if (address % 16 == 0) {
            USBSerial.printf("%02x: ", address);
        }
        
        Wire.beginTransmission(address);
        uint8_t error = Wire.endTransmission();
        
        if (error == 0) {
            USBSerial.printf("%02x ", address);
            devicesFound++;
            
            if (address == 0x3C || address == 0x3D) {
                USBSerial.printf("← OLED! ");
            } else if (address == 0x51) {
                USBSerial.printf("← RTC! ");
            } else {
                USBSerial.printf("← Device! ");
            }
        } else {
            USBSerial.print("-- ");
        }
        
        if ((address + 1) % 16 == 0) {
            USBSerial.println();
        }
        delay(2);
    }
    
    USBSerial.println();
    USBSerial.printf("🎯 Found %d I2C device(s)\n", devicesFound);
}

// Function to test I2C configurations
void testI2CConfigurations() {
    USBSerial.println("🔧 Testing multiple I2C configurations and speeds...");
    
    // Test different clock speeds
    uint32_t speeds[] = {10000, 50000, 100000, 400000};
    const char* speedNames[] = {"10kHz", "50kHz", "100kHz", "400kHz"};
    
    for (int s = 0; s < 4; s++) {
        USBSerial.printf("\n--- Testing %s clock speed ---\n", speedNames[s]);
        
        // Config 1: SDA=5, SCL=4
        USBSerial.printf("Config 1: SDA=5, SCL=4 @ %s\n", speedNames[s]);
        Wire.end();
        Wire.begin(5, 4);
        Wire.setClock(speeds[s]);
        delay(200);
        
        Wire.beginTransmission(0x51);
        uint8_t test1 = Wire.endTransmission();
        USBSerial.printf("  RTC (0x51): %s\n", test1 == 0 ? "✅ OK" : "❌ NACK");
        
        Wire.beginTransmission(0x3C);
        uint8_t test1b = Wire.endTransmission();
        USBSerial.printf("  OLED (0x3C): %s\n", test1b == 0 ? "✅ OK" : "❌ NACK");
        
        // Config 2: Try swapped pins
        USBSerial.printf("Config 2: SDA=4, SCL=5 @ %s\n", speedNames[s]);
        Wire.end();
        Wire.begin(4, 5);
        Wire.setClock(speeds[s]);
        delay(200);
        
        Wire.beginTransmission(0x51);
        uint8_t test2 = Wire.endTransmission();
        USBSerial.printf("  RTC (0x51): %s\n", test2 == 0 ? "✅ OK" : "❌ NACK");
        
        Wire.beginTransmission(0x3C);
        uint8_t test2b = Wire.endTransmission();
        USBSerial.printf("  OLED (0x3C): %s\n", test2b == 0 ? "✅ OK" : "❌ NACK");
        
        // Config 3: Try other common pin combinations
        USBSerial.printf("Config 3: SDA=21, SCL=22 @ %s\n", speedNames[s]);
        Wire.end();
        Wire.begin(21, 22);
        Wire.setClock(speeds[s]);
        delay(200);
        
        Wire.beginTransmission(0x51);
        uint8_t test3 = Wire.endTransmission();
        USBSerial.printf("  RTC (0x51): %s\n", test3 == 0 ? "✅ OK" : "❌ NACK");
    }
    
    // Restore original configuration
    Wire.end();
    Wire.begin(OLED_SDA, OLED_SCL);
    Wire.setClock(100000);
    delay(100);
    USBSerial.println("\n🔄 Restored to SDA=5, SCL=4 @ 100kHz");
}
