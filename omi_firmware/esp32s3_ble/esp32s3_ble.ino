/*
 * XIAO ESP32S3 Sense - Enhanced Brutal Honest AI Firmware
 * Features: Button-controlled recording, Display control, SD storage, WiFi sync, Whisper transcription
 */

#include "BLEDevice.h"
#include "BLEServer.h"
#include "BLEUtils.h"
#include "BLE2902.h"
#include "driver/i2s.h"
#include "WiFi.h"
#include "WebServer.h"
#include "SD.h"
#include "SPI.h"
#include "FS.h"
#include "esp_heap_caps.h"
#include "esp_task_wdt.h"
#include "Wire.h"
#include "U8g2lib.h"

// BLE Configuration
#define SERVICE_UUID        "12345678-1234-1234-1234-123456789abc"
#define AUDIO_CHAR_UUID     "12345678-1234-1234-1234-123456789abd"
#define STATUS_CHAR_UUID    "12345678-1234-1234-1234-123456789abe"
#define FILE_CHAR_UUID      "12345678-1234-1234-1234-123456789abf"
#define TRANSCRIPTION_CHAR_UUID "12345678-1234-1234-1234-123456789ac0"

// Hardware Configuration - XIAO ESP32S3 Sense + Expansion Board
#define LED_PIN LED_BUILTIN
#define BUTTON_PIN 2        // User button on expansion board (CONFIRMED: Pin 2)
#define BUZZER_PIN 3        // Buzzer on expansion board (CONFIRMED: Pin 3)
#define DISPLAY_POWER_PIN 6 // Display power control on expansion board
#define SD_CS_PIN 21        // SD card chip select on expansion board
#define SD_MOSI_PIN 10      // SD card MOSI
#define SD_MISO_PIN 9       // SD card MISO  
#define SD_SCK_PIN 8        // SD card SCK

// Display Configuration (I2C OLED on Expansion Board) - Based on Seeed Studio docs
int DISPLAY_SDA_PIN = 5;   // I2C SDA for OLED display (Pin 5 on XIAO Expansion Board)
int DISPLAY_SCL_PIN = 4;   // I2C SCL for OLED display (Pin 4 on XIAO Expansion Board)
#define DISPLAY_WIDTH 128
#define DISPLAY_HEIGHT 64
#define OLED_ADDRESS 0x3C  // Standard OLED I2C address

// Audio Configuration
#define SAMPLE_RATE 16000
#define BUFFER_SIZE 1024
#define RECORDING_DURATION_MS 30000  // 30 seconds max per recording

// I2S Configuration for ESP32S3 Sense built-in microphone
#define I2S_WS 42
#define I2S_SD 41
#define I2S_SCK 2

// Global Variables
BLEServer* pServer = nullptr;
BLECharacteristic* pAudioCharacteristic = nullptr;
BLECharacteristic* pStatusCharacteristic = nullptr;
BLECharacteristic* pFileCharacteristic = nullptr;
BLECharacteristic* pTranscriptionCharacteristic = nullptr;
bool deviceConnected = false;
bool wifiConnected = false;

// Button and Recording State
volatile bool buttonPressed = false;
volatile bool recording = false;
volatile unsigned long buttonPressTime = 0;
volatile unsigned long recordingStartTime = 0;

// Display State
bool displayOn = false;
U8G2_SSD1306_128X64_NONAME_F_HW_I2C display(U8G2_R0, /* reset=*/ U8X8_PIN_NONE);

// Audio buffers
int16_t audioBuffer[BUFFER_SIZE];
uint8_t bleBuffer[BUFFER_SIZE * 2 + 4];
int16_t* recordingBuffer = nullptr;
size_t recordingBufferSize = 0;
size_t recordingIndex = 0;

// File management
String currentRecordingFile = "";
int recordingCounter = 0;

// Transcription and Voice Activity Detection
bool transcriptionEnabled = true;
float voiceThreshold = 1000.0;  // Adjust based on testing
String lastTranscription = "";
bool voiceDetected = false;

// WiFi and Web Server
WebServer server(80);
const char* ssid = "OMI-ESP32S3";  // AP mode SSID
const char* password = "brutalhonest";  // AP mode password

// Button interrupt handler
void IRAM_ATTR buttonISR() {
    unsigned long currentTime = millis();
    if (currentTime - buttonPressTime > 200) {  // Debounce 200ms
        buttonPressed = true;
        buttonPressTime = currentTime;
        // Note: Can't use Serial.println in ISR, will debug in main loop
    }
}

class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
        deviceConnected = true;
        digitalWrite(LED_PIN, HIGH);
        Serial.println("BLE Client connected");
        
        // Send status
        if (pStatusCharacteristic) {
            String status = "ESP32S3_CONNECTED|SD:" + String(SD.cardType() != CARD_NONE ? "OK" : "NONE") + "|WiFi:" + String(wifiConnected ? "OK" : "AP");
            pStatusCharacteristic->setValue(status.c_str());
            pStatusCharacteristic->notify();
        }
    }

    void onDisconnect(BLEServer* pServer) {
        deviceConnected = false;
        digitalWrite(LED_PIN, LOW);
        Serial.println("BLE Client disconnected");
        
        // Restart advertising
        pServer->getAdvertising()->start();
    }
};

void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("Starting XIAO ESP32S3 Sense - Enhanced Brutal Honest AI");
    Serial.println("=== HARDWARE DEBUG INFORMATION ===");
    
    // Initialize hardware pins with debugging
    Serial.println("Initializing hardware pins...");
    pinMode(LED_PIN, OUTPUT);
    pinMode(BUTTON_PIN, INPUT_PULLUP);
    pinMode(BUZZER_PIN, OUTPUT);
    pinMode(DISPLAY_POWER_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);
    digitalWrite(BUZZER_PIN, LOW);
    digitalWrite(DISPLAY_POWER_PIN, HIGH);  // Turn on display power
    Serial.println("LED, Button (Pin 2), Buzzer (Pin 3) initialized");
    
    Serial.printf("LED_PIN: %d (set to OUTPUT, LOW)\n", LED_PIN);
    Serial.printf("BUTTON_PIN: %d (set to INPUT_PULLUP)\n", BUTTON_PIN);
    Serial.printf("DISPLAY_POWER_PIN: %d (set to OUTPUT, HIGH)\n", DISPLAY_POWER_PIN);
    Serial.printf("SD_CS_PIN: %d\n", SD_CS_PIN);
    Serial.printf("SD_MOSI_PIN: %d\n", SD_MOSI_PIN);
    Serial.printf("SD_MISO_PIN: %d\n", SD_MISO_PIN);
    Serial.printf("SD_SCK_PIN: %d\n", SD_SCK_PIN);
    
    // Test button pin reading
    Serial.printf("Initial button state: %s (pin value: %d)\n", 
                  digitalRead(BUTTON_PIN) ? "NOT_PRESSED" : "PRESSED", 
                  digitalRead(BUTTON_PIN));
    
    // Scan all possible button pins on expansion board
    Serial.println("[DEBUG] === BUTTON PIN SCANNER ===");
    Serial.println("[DEBUG] Scanning common expansion board pins for button...");
    int testPins[] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 43, 44, 45, 46, 47, 48};
    int numPins = sizeof(testPins) / sizeof(testPins[0]);
    
    for (int i = 0; i < numPins; i++) {
        int pin = testPins[i];
        pinMode(pin, INPUT_PULLUP);
        delay(10);
        int value = digitalRead(pin);
        Serial.printf("[DEBUG] Pin %d: %s (%d)\n", pin, value ? "HIGH" : "LOW", value);
    }
    Serial.println("[DEBUG] === BUTTON PIN SCANNER COMPLETE ===");
    Serial.println("[DEBUG] Press button now and watch for pin changes!");
    
    // Initialize OLED Display (using standard XIAO Expansion Board pins)
    Serial.println("✅ === OLED DISPLAY INITIALIZATION ===");
    Serial.printf("✅ Using XIAO Expansion Board standard pins: SDA=%d, SCL=%d\n", DISPLAY_SDA_PIN, DISPLAY_SCL_PIN);
    
    // Initialize display with the standard pins first
    initializeDisplay();
    
    // If that fails, try alternative pin combinations
    if (!displayOn) {
        Serial.println("⚠️ Standard pins failed, trying alternative I2C pin combinations...");
        
        // Alternative I2C pin combinations for XIAO Expansion Board
        int sdaPins[] = {4, 6, 7, 20, 21};  // Alternative SDA pins
        int sclPins[] = {5, 7, 6, 21, 20};  // Alternative SCL pins
        int numCombos = sizeof(sdaPins) / sizeof(sdaPins[0]);
        
        for (int i = 0; i < numCombos && !displayOn; i++) {
            int sda = sdaPins[i];
            int scl = sclPins[i];
            
            Serial.printf("⚠️ Trying alternative pins: SDA=%d, SCL=%d\n", sda, scl);
            
            // Update pins and try again
            DISPLAY_SDA_PIN = sda;
            DISPLAY_SCL_PIN = scl;
            
            initializeDisplay();
            
            if (displayOn) {
                Serial.printf("✅ Display working on alternative pins: SDA=%d, SCL=%d\n", sda, scl);
                break;
            }
        }
    }
    
    if (!displayOn) {
        Serial.println("❌ OLED display not found on any pin combination");
        Serial.println("❌ Continuing without display - check hardware connections");
    }
    Serial.println("✅ === DISPLAY INITIALIZATION COMPLETE ===");
    
    // Setup button interrupt with debugging
    Serial.println("Setting up button interrupt...");
    int interruptPin = digitalPinToInterrupt(BUTTON_PIN);
    Serial.printf("Button interrupt pin: %d (for GPIO %d)\n", interruptPin, BUTTON_PIN);
    
    if (interruptPin == NOT_A_PIN) {
        Serial.println("ERROR: Button pin does not support interrupts!");
    } else {
        attachInterrupt(interruptPin, buttonISR, FALLING);
        Serial.println("Button interrupt attached successfully (FALLING edge)");
    }
    
    // Initialize SD card
    initializeSD();
    
    // Initialize I2S microphone
    initializeI2S();
    
    // Allocate recording buffer (30 seconds at 16kHz)
    recordingBufferSize = SAMPLE_RATE * (RECORDING_DURATION_MS / 1000);
    recordingBuffer = (int16_t*)heap_caps_malloc(recordingBufferSize * sizeof(int16_t), MALLOC_CAP_SPIRAM);
    if (!recordingBuffer) {
        Serial.println("Failed to allocate recording buffer in PSRAM, trying internal RAM");
        recordingBuffer = (int16_t*)malloc(recordingBufferSize * sizeof(int16_t));
        if (!recordingBuffer) {
            Serial.println("Failed to allocate recording buffer!");
            recordingBufferSize = BUFFER_SIZE * 10;  // Fallback to smaller buffer
            recordingBuffer = (int16_t*)malloc(recordingBufferSize * sizeof(int16_t));
        }
    }
    
    // Initialize WiFi in AP mode
    initializeWiFi();
    
    // Initialize BLE
    initializeBLE();
    
    Serial.println("All systems initialized - Device ready!");
    Serial.println("*** BRUTAL HONEST QUERY SYSTEM READY ***");
    Serial.println("Press button (Pin 2) to record your Brutal Honest Query!");
    
    // Startup sequence with LED and buzzer
    for (int i = 0; i < 3; i++) {
        digitalWrite(LED_PIN, HIGH);
        digitalWrite(BUZZER_PIN, HIGH);
        delay(200);
        digitalWrite(LED_PIN, LOW);
        digitalWrite(BUZZER_PIN, LOW);
        delay(200);
    }
}

void loop() {
    static unsigned long lastDebugTime = 0;
    static unsigned long loopCount = 0;
    static int lastButtonState = HIGH;
    static unsigned long lastPinScan = 0;
    static int lastPinStates[17] = {-1}; // Initialize to -1 (unread)
    
    loopCount++;
    
    // Debug button state changes on configured pin
    int currentButtonState = digitalRead(BUTTON_PIN);
    if (currentButtonState != lastButtonState) {
        Serial.printf("[DEBUG] Button state changed: %s (pin value: %d) at loop %lu\n", 
                      currentButtonState ? "RELEASED" : "PRESSED", 
                      currentButtonState, loopCount);
        lastButtonState = currentButtonState;
    }
    
    // Scan all pins for changes every 50ms to detect button presses (more responsive)
    if (millis() - lastPinScan > 50) {
        int testPins[] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 43, 44, 45, 46, 47, 48};
        int numPins = sizeof(testPins) / sizeof(testPins[0]);
        
        for (int i = 0; i < numPins; i++) {
            int pin = testPins[i];
            int currentState = digitalRead(pin);
            
            // Check if this is the first read or if state changed
            if (lastPinStates[i] == -1) {
                lastPinStates[i] = currentState; // Initialize
            } else if (currentState != lastPinStates[i]) {
                Serial.printf("[BUTTON DETECTED] Pin %d changed: %s -> %s\n", 
                              pin, 
                              lastPinStates[i] ? "HIGH" : "LOW",
                              currentState ? "HIGH" : "LOW");
                
                // If this looks like a button press (HIGH to LOW), trigger recording
                if (lastPinStates[i] == HIGH && currentState == LOW) {
                    Serial.printf("[BUTTON PRESS] Detected button press on pin %d!\n", pin);
                    // Manually trigger button press handler
                    handleButtonPress();
                }
                
                lastPinStates[i] = currentState;
            }
        }
        lastPinScan = millis();
    }
    
    // Handle button press
    if (buttonPressed) {
        Serial.printf("[DEBUG] Button press detected! Time since last: %lu ms\n", 
                      millis() - buttonPressTime);
        buttonPressed = false;
        handleButtonPress();
    }
    
    // Handle recording with transcription
    if (recording) {
        handleRecordingWithTranscription();
    }
    
    // Handle WiFi server
    server.handleClient();
    
    // Status LED management
    handleStatusLED();
    
    // Check for recording timeout
    if (recording && (millis() - recordingStartTime > RECORDING_DURATION_MS)) {
        Serial.println("[DEBUG] Recording timeout reached, stopping...");
        stopRecording();
    }
    
    // Update display periodically
    static unsigned long lastDisplayUpdate = 0;
    if (displayOn && (millis() - lastDisplayUpdate > 1000)) {  // Update every second
        updateDisplay();
        lastDisplayUpdate = millis();
    }
    
    // Periodic debug info every 10 seconds
    if (millis() - lastDebugTime > 10000) {
        Serial.printf("[DEBUG] Loop %lu - Button: %s, Recording: %s, BLE: %s, WiFi: %s\n",
                      loopCount,
                      digitalRead(BUTTON_PIN) ? "HIGH" : "LOW",
                      recording ? "YES" : "NO",
                      deviceConnected ? "CONNECTED" : "DISCONNECTED",
                      "AP_MODE");
        Serial.printf("[DEBUG] Free heap: %d bytes, Recording count: %d\n", 
                      ESP.getFreeHeap(), recordingCounter);
        
        // Show current state of all pins
        Serial.println("[PIN STATUS] Current pin states:");
        int testPins[] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 43, 44, 45, 46, 47, 48};
        int numPins = sizeof(testPins) / sizeof(testPins[0]);
        for (int i = 0; i < numPins; i++) {
            int pin = testPins[i];
            int value = digitalRead(pin);
            Serial.printf("[PIN STATUS] Pin %d: %s ", pin, value ? "HIGH" : "LOW");
            if ((i + 1) % 6 == 0) Serial.println(); // New line every 6 pins
        }
        Serial.println();
        Serial.println("[INSTRUCTION] Press button now to see pin changes!");
        
        // Check SD card for recorded files
        Serial.println("[SD STATUS] Checking SD card files...");
        File root = SD.open("/");
        if (root) {
            Serial.println("[SD STATUS] Root directory contents:");
            File file = root.openNextFile();
            int fileCount = 0;
            while (file) {
                if (file.isDirectory()) {
                    Serial.printf("[SD STATUS] DIR: %s\n", file.name());
                } else {
                    Serial.printf("[SD STATUS] FILE: %s (%d bytes)\n", file.name(), file.size());
                }
                file = root.openNextFile();
                fileCount++;
            }
            root.close();
            
            // Also try to check recordings directory
            File recDir = SD.open("/recordings");
            if (recDir) {
                Serial.println("[SD STATUS] /recordings directory contents:");
                File recFile = recDir.openNextFile();
                int recCount = 0;
                while (recFile) {
                    Serial.printf("[SD STATUS] REC: %s (%d bytes)\n", recFile.name(), recFile.size());
                    recFile = recDir.openNextFile();
                    recCount++;
                }
                if (recCount == 0) {
                    Serial.println("[SD STATUS] No files in /recordings directory");
                }
                recDir.close();
            } else {
                Serial.println("[SD STATUS] /recordings directory not accessible");
            }
        } else {
            Serial.println("[SD STATUS] Could not open SD card root directory");
        }
        
        lastDebugTime = millis();
    }
    
    delay(1);
}

void initializeI2S() {
    Serial.println("Initializing I2S microphone...");
    
    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate = SAMPLE_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 4,
        .dma_buf_len = 1024,
        .use_apll = false,
        .tx_desc_auto_clear = false,
        .fixed_mclk = 0
    };
    
    i2s_pin_config_t pin_config = {
        .bck_io_num = I2S_SCK,
        .ws_io_num = I2S_WS,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num = I2S_SD
    };
    
    esp_err_t result = i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
    if (result != ESP_OK) {
        Serial.printf("I2S driver install failed: %d\n", result);
        return;
    }
    
    result = i2s_set_pin(I2S_NUM_0, &pin_config);
    if (result != ESP_OK) {
        Serial.printf("I2S set pin failed: %d\n", result);
        return;
    }
    
    Serial.println("I2S microphone initialized successfully");
}

void initializeBLE() {
    Serial.println("Initializing BLE...");
    
    BLEDevice::init("OMI-ESP32S3-BrutalAI");
    pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());
    
    BLEService *pService = pServer->createService(SERVICE_UUID);
    
    // Audio characteristic
    pAudioCharacteristic = pService->createCharacteristic(
        AUDIO_CHAR_UUID,
        BLECharacteristic::PROPERTY_NOTIFY
    );
    pAudioCharacteristic->addDescriptor(new BLE2902());
    
    // Status characteristic
    pStatusCharacteristic = pService->createCharacteristic(
        STATUS_CHAR_UUID,
        BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
    );
    pStatusCharacteristic->addDescriptor(new BLE2902());
    
    // File transfer characteristic
    pFileCharacteristic = pService->createCharacteristic(
        FILE_CHAR_UUID,
        BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
    );
    pFileCharacteristic->addDescriptor(new BLE2902());
    
    // Transcription characteristic
    pTranscriptionCharacteristic = pService->createCharacteristic(
        TRANSCRIPTION_CHAR_UUID,
        BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
    );
    pTranscriptionCharacteristic->addDescriptor(new BLE2902());
    
    pService->start();
    
    BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->setScanResponse(true);
    pAdvertising->setMinPreferred(0x06);
    pAdvertising->setMinPreferred(0x12);
    pAdvertising->start();
    
    Serial.println("BLE initialized successfully");
}

// Initialize OLED Display
void initializeDisplay() {
    Serial.println("✅ Initializing OLED display...");
    
    // Ensure display power is on
    digitalWrite(DISPLAY_POWER_PIN, HIGH);
    delay(100);  // Give display time to power up
    
    // Initialize I2C with correct pins for XIAO Expansion Board
    Wire.end();  // End any previous I2C session
    delay(50);
    
    Serial.printf("✅ Starting I2C on SDA=%d, SCL=%d\n", DISPLAY_SDA_PIN, DISPLAY_SCL_PIN);
    Wire.begin(DISPLAY_SDA_PIN, DISPLAY_SCL_PIN);
    Wire.setClock(100000);  // Set I2C clock to 100kHz (more reliable)
    delay(100);
    
    // Scan for I2C devices
    Serial.println("✅ Scanning I2C bus for OLED display...");
    bool deviceFound = false;
    
    for (int addr = 0x3C; addr <= 0x3D; addr++) {
        Wire.beginTransmission(addr);
        uint8_t error = Wire.endTransmission();
        
        if (error == 0) {
            Serial.printf("✅ I2C device found at address 0x%02X\n", addr);
            deviceFound = true;
            break;
        } else {
            Serial.printf("❌ No device at 0x%02X (error: %d)\n", addr, error);
        }
        delay(10);
    }
    
    if (!deviceFound) {
        Serial.println("❌ No I2C devices found - OLED display not detected");
        displayOn = false;
        return;
    }
    
    // Initialize U8g2 display
    Serial.println("✅ Attempting U8g2 display initialization...");
    
    // Try different initialization methods
    bool displayInitialized = false;
    
    // Method 1: Standard initialization
    if (!displayInitialized) {
        Serial.println("✅ Trying standard U8g2 initialization...");
        if (display.begin()) {
            displayInitialized = true;
            Serial.println("✅ Standard initialization successful");
        } else {
            Serial.println("❌ Standard initialization failed");
        }
    }
    
    // Method 2: Manual initialization with specific settings
    if (!displayInitialized) {
        Serial.println("✅ Trying manual U8g2 initialization...");
        display.initDisplay();
        display.setPowerSave(0);  // Wake up display
        displayInitialized = true;
        Serial.println("✅ Manual initialization completed");
    }
    
    if (displayInitialized) {
        // Clear display and show startup message
        display.clearBuffer();
        display.setFont(u8g2_font_ncenB08_tr);
        
        // Test display by drawing text
        display.drawStr(0, 15, "Brutal Honest");
        display.drawStr(0, 30, "Query System");
        display.drawStr(0, 45, "Ready!");
        display.sendBuffer();
        
        displayOn = true;
        Serial.println("✅ OLED initialized with U8X8!");
        
        // Brief display test
        delay(1000);
        display.clearBuffer();
        display.drawStr(0, 15, "Display Test");
        display.drawStr(0, 30, "Working!");
        display.sendBuffer();
        delay(1000);
        
    } else {
        Serial.println("❌ OLED display initialization failed - continuing without display");
        displayOn = false;
    }
}

// Update display with current status
void updateDisplay() {
    if (!displayOn) {
        // Just print status to serial if no display
        String status = "";
        if (recording) {
            unsigned long recordTime = (millis() - recordingStartTime) / 1000;
            status = "Recording... Time: " + String(recordTime) + "s";
        } else if (deviceConnected) {
            status = "BLE Connected";
        } else {
            status = "Ready - Press button to record";
        }
        Serial.println("📱 Status: " + status);
        return;
    }
    
    // Only update display if it was successfully initialized
    Serial.println("📱 Updating OLED display...");
    
    // Clear display buffer
    display.clearBuffer();
    display.setFont(u8g2_font_ncenB08_tr);
    
    // Title - Show "Brutal Honest Query"
    display.drawStr(0, 12, "Brutal Honest AI");
    
    // Status line
    String status = "";
    if (recording) {
        status = "Recording...";
        // Show recording time
        unsigned long recordTime = (millis() - recordingStartTime) / 1000;
        display.drawStr(0, 28, status.c_str());
        display.drawStr(0, 44, ("Time: " + String(recordTime) + "s").c_str());
        Serial.printf("📱 Display: %s (Time: %lus)\n", status.c_str(), recordTime);
    } else if (deviceConnected) {
        status = "BLE Connected";
        display.drawStr(0, 28, status.c_str());
        display.drawStr(0, 44, "Ready to sync");
        Serial.println("📱 Display: BLE Connected");
    } else {
        status = "Ready";
        display.drawStr(0, 28, status.c_str());
        display.drawStr(0, 44, "Press button");
        Serial.println("📱 Display: Ready - Press button");
    }
    
    // Show SD card status
    if (SD.cardType() != CARD_NONE) {
        String fileStatus = "Files: " + String(recordingCounter);
        display.drawStr(0, 60, fileStatus.c_str());
        Serial.printf("📱 Display: %s\n", fileStatus.c_str());
    } else {
        display.drawStr(0, 60, "No SD Card");
        Serial.println("📱 Display: No SD Card");
    }
    
    // Send buffer to display
    display.sendBuffer();
    Serial.println("📱 Display updated successfully");
}

// Turn display on/off
void setDisplayPower(bool on) {
    if (on && !displayOn) {
        Serial.println("🔌 Turning display ON...");
        digitalWrite(DISPLAY_POWER_PIN, HIGH);
        delay(200);  // Give display time to power up
        
        // Try to reinitialize display
        initializeDisplay();
        
        if (displayOn) {
            Serial.println("✅ Display turned ON successfully");
            updateDisplay();
        } else {
            Serial.println("❌ Failed to turn display ON");
        }
    } else if (!on && displayOn) {
        Serial.println("🔌 Turning display OFF...");
        display.setPowerSave(1);  // Put display to sleep
        digitalWrite(DISPLAY_POWER_PIN, LOW);
        displayOn = false;
        Serial.println("✅ Display turned OFF");
    }
}

void sendAudioViaBLE(int16_t* audioData, size_t sampleCount, uint32_t timestamp) {
    if (!deviceConnected || !pAudioCharacteristic) return;
    
    // Pack timestamp (4 bytes) + audio data
    bleBuffer[0] = (timestamp >> 24) & 0xFF;
    bleBuffer[1] = (timestamp >> 16) & 0xFF;
    bleBuffer[2] = (timestamp >> 8) & 0xFF;
    bleBuffer[3] = timestamp & 0xFF;
    
    // Copy audio data
    memcpy(&bleBuffer[4], audioData, sampleCount * 2);
    
    size_t totalSize = 4 + (sampleCount * 2);
    if (totalSize <= 512) { // BLE MTU limit
        pAudioCharacteristic->setValue(bleBuffer, totalSize);
        pAudioCharacteristic->notify();
    }
}

// Send audio data via USB Serial for local hub
void sendAudioViaUSB(int16_t* samples, size_t sampleCount) {
    if (!samples || sampleCount == 0) return;
    
    // Send raw audio bytes via Serial
    // The hub server will collect these bytes and reconstruct the audio
    Serial.write((uint8_t*)samples, sampleCount * 2);
}

// Initialize SD card
void initializeSD() {
    Serial.println("[DEBUG] === SD CARD INITIALIZATION ===");
    Serial.printf("[DEBUG] SD pins - CS: %d, MOSI: %d, MISO: %d, SCK: %d\n", 
                  SD_CS_PIN, SD_MOSI_PIN, SD_MISO_PIN, SD_SCK_PIN);
    
    Serial.println("[DEBUG] Initializing SPI for SD card...");
    SPI.begin(SD_SCK_PIN, SD_MISO_PIN, SD_MOSI_PIN, SD_CS_PIN);
    
    Serial.println("[DEBUG] Attempting SD.begin()...");
    if (!SD.begin(SD_CS_PIN)) {
        Serial.println("[ERROR] SD card initialization failed!");
        Serial.println("[DEBUG] Possible causes:");
        Serial.println("[DEBUG] - No SD card inserted");
        Serial.println("[DEBUG] - SD card not formatted");
        Serial.println("[DEBUG] - Wrong pin configuration");
        Serial.println("[DEBUG] - Faulty SD card");
        return;
    }
    
    uint8_t cardType = SD.cardType();
    Serial.printf("[DEBUG] SD card type value: %d\n", cardType);
    
    if (cardType == CARD_NONE) {
        Serial.println("[ERROR] No SD card attached");
        return;
    }
    
    Serial.print("[DEBUG] SD Card Type: ");
    if (cardType == CARD_MMC) {
        Serial.println("MMC");
    } else if (cardType == CARD_SD) {
        Serial.println("SDSC");
    } else if (cardType == CARD_SDHC) {
        Serial.println("SDHC");
    } else {
        Serial.printf("UNKNOWN (%d)\n", cardType);
    }
    
    uint64_t cardSize = SD.cardSize() / (1024 * 1024);
    Serial.printf("[DEBUG] SD Card Size: %lluMB\n", cardSize);
    
    // Create recordings directory
    Serial.println("[DEBUG] Creating /recordings directory...");
    if (!SD.exists("/recordings")) {
        if (SD.mkdir("/recordings")) {
            Serial.println("[DEBUG] /recordings directory created successfully");
        } else {
            Serial.println("[ERROR] Failed to create /recordings directory");
        }
    } else {
        Serial.println("[DEBUG] /recordings directory already exists");
    }
    
    // List existing files
    Serial.println("[DEBUG] Listing existing files in /recordings:");
    File root = SD.open("/recordings");
    if (root) {
        File file = root.openNextFile();
        int fileCount = 0;
        while (file) {
            Serial.printf("[DEBUG] - %s (%d bytes)\n", file.name(), file.size());
            fileCount++;
            file = root.openNextFile();
        }
        Serial.printf("[DEBUG] Total files found: %d\n", fileCount);
        root.close();
    } else {
        Serial.println("[ERROR] Failed to open /recordings directory");
    }
    
    Serial.println("[DEBUG] === SD CARD INITIALIZATION COMPLETE ===");
}

// Initialize WiFi in AP mode
void initializeWiFi() {
    Serial.println("Initializing WiFi AP...");
    
    WiFi.mode(WIFI_AP);
    WiFi.softAP(ssid, password);
    
    IPAddress IP = WiFi.softAPIP();
    Serial.print("AP IP address: ");
    Serial.println(IP);
    
    // Setup web server routes
    server.on("/", handleRoot);
    server.on("/list", handleFileList);
    server.on("/download", handleFileDownload);
    // server.on("/transcriptions", handleTranscriptionList); // Temporarily disabled
    server.on("/status", handleStatus);
    server.begin();
    
    Serial.println("WiFi AP and web server started");
}

// Handle button press
void handleButtonPress() {
    Serial.println("[DEBUG] === BUTTON PRESS HANDLER ===");
    Serial.printf("[DEBUG] Current time: %lu ms\n", millis());
    Serial.printf("[DEBUG] Button pin state: %d\n", digitalRead(BUTTON_PIN));
    Serial.printf("[DEBUG] Current recording state: %s\n", recording ? "RECORDING" : "IDLE");
    Serial.printf("[DEBUG] Display state: %s\n", displayOn ? "ON" : "OFF");
    
    // Buzzer feedback for button press
    digitalWrite(BUZZER_PIN, HIGH);
    delay(100);
    digitalWrite(BUZZER_PIN, LOW);
    Serial.println("[DEBUG] Buzzer feedback provided");
    
    // Turn on display if it's off
    if (!displayOn) {
        Serial.println("[DEBUG] Turning on display...");
        setDisplayPower(true);
    }
    
    // Toggle recording
    if (!recording) {
        Serial.println("[DEBUG] Starting new recording...");
        startRecording();
    } else {
        Serial.println("[DEBUG] Stopping current recording...");
        stopRecording();
    }
    
    // Update display
    updateDisplay();
    Serial.println("[DEBUG] === BUTTON PRESS HANDLER COMPLETE ===");
}

// Start recording
void startRecording() {
    Serial.println("[DEBUG] === START RECORDING ===");
    
    if (!recordingBuffer) {
        Serial.println("[ERROR] Recording buffer not available!");
        return;
    }
    
    Serial.printf("[DEBUG] Recording buffer available: %d samples\n", recordingBufferSize);
    
    recording = true;
    recordingIndex = 0;
    recordingStartTime = millis();
    voiceDetected = false;  // Reset voice detection for new recording
    
    // Generate filename
    recordingCounter++;
    currentRecordingFile = "/recordings/rec_" + String(recordingCounter) + ".wav";
    
    Serial.printf("[DEBUG] Recording #%d started: %s\n", recordingCounter, currentRecordingFile.c_str());
    Serial.printf("[DEBUG] Recording start time: %lu ms\n", recordingStartTime);
    Serial.printf("[DEBUG] Max recording duration: %d ms\n", RECORDING_DURATION_MS);
    
    // Fast LED blink during recording
    digitalWrite(LED_PIN, HIGH);
    Serial.println("[DEBUG] LED turned ON for recording indication");
    
    // Send USB audio start marker
    Serial.println("AUDIO_START");
    
    // Notify status
    if (pStatusCharacteristic && deviceConnected) {
        pStatusCharacteristic->setValue("RECORDING");
        pStatusCharacteristic->notify();
        Serial.println("[DEBUG] BLE status updated: RECORDING");
    }
    
    // Update display
    updateDisplay();
    Serial.println("[DEBUG] === START RECORDING COMPLETE ===");
}

// Stop recording and save to SD card
void stopRecording() {
    if (!recording) return;
    
    recording = false;
    digitalWrite(LED_PIN, LOW);
    
    // Send USB audio end marker
    Serial.println("AUDIO_END");
    
    Serial.println("Recording stopped. Samples recorded: " + String(recordingIndex));
    
    // Save to SD card as WAV file
    if (SD.cardType() != CARD_NONE && recordingIndex > 0) {
        saveWAVFile();
    }
    
    // Process transcription if voice was detected
    if (transcriptionEnabled && voiceDetected) {
        processTranscription();
    }
    
    // Notify status
    if (pStatusCharacteristic && deviceConnected) {
        String status = "SAVED:" + currentRecordingFile;
        if (voiceDetected) status += "|VOICE_DETECTED";
        pStatusCharacteristic->setValue(status.c_str());
        pStatusCharacteristic->notify();
    }
    
    Serial.println("Recording saved to: " + currentRecordingFile);
    if (voiceDetected) {
        Serial.println("Voice activity was detected in recording");
    }
    
    // Update display
    updateDisplay();
}

// Handle recording process
void handleRecording() {
    if (!recording || !recordingBuffer) return;
    
    size_t bytesRead = 0;
    esp_err_t result = i2s_read(I2S_NUM_0, audioBuffer, sizeof(audioBuffer), &bytesRead, 10);
    
    if (result == ESP_OK && bytesRead > 0) {
        size_t samplesRead = bytesRead / 2;
        
        // Store in recording buffer
        for (size_t i = 0; i < samplesRead && recordingIndex < recordingBufferSize; i++) {
            recordingBuffer[recordingIndex++] = audioBuffer[i];
        }
        
        // Also send via BLE if connected
        if (deviceConnected) {
            uint32_t timestamp = millis();
            sendAudioViaBLE(audioBuffer, samplesRead, timestamp);
        }
        
        // Send audio data via USB Serial for local hub
        sendAudioViaUSB(audioBuffer, samplesRead);
        
        // Check if buffer is full
        if (recordingIndex >= recordingBufferSize) {
            stopRecording();
        }
    }
}

// Handle status LED
void handleStatusLED() {
    static unsigned long lastBlink = 0;
    static bool ledState = false;
    
    if (recording) {
        // Fast blink during recording
        if (millis() - lastBlink > 100) {
            ledState = !ledState;
            digitalWrite(LED_PIN, ledState);
            lastBlink = millis();
        }
    } else if (!deviceConnected && !wifiConnected) {
        // Slow blink when not connected
        if (millis() - lastBlink > 1000) {
            ledState = !ledState;
            digitalWrite(LED_PIN, ledState);
            lastBlink = millis();
        }
    }
}

// Save WAV file to SD card
void saveWAVFile() {
    File file = SD.open(currentRecordingFile, FILE_WRITE);
    if (!file) {
        Serial.println("Failed to create file: " + currentRecordingFile);
        return;
    }
    
    // WAV header
    uint32_t dataSize = recordingIndex * 2;
    uint32_t fileSize = dataSize + 36;
    
    // RIFF header
    file.write((uint8_t*)"RIFF", 4);
    file.write((uint8_t*)&fileSize, 4);
    file.write((uint8_t*)"WAVE", 4);
    
    // fmt chunk
    file.write((uint8_t*)"fmt ", 4);
    uint32_t fmtSize = 16;
    file.write((uint8_t*)&fmtSize, 4);
    uint16_t audioFormat = 1; // PCM
    file.write((uint8_t*)&audioFormat, 2);
    uint16_t numChannels = 1;
    file.write((uint8_t*)&numChannels, 2);
    uint32_t sampleRate = SAMPLE_RATE;
    file.write((uint8_t*)&sampleRate, 4);
    uint32_t byteRate = SAMPLE_RATE * 2;
    file.write((uint8_t*)&byteRate, 4);
    uint16_t blockAlign = 2;
    file.write((uint8_t*)&blockAlign, 2);
    uint16_t bitsPerSample = 16;
    file.write((uint8_t*)&bitsPerSample, 2);
    
    // data chunk
    file.write((uint8_t*)"data", 4);
    file.write((uint8_t*)&dataSize, 4);
    
    // Write audio data
    file.write((uint8_t*)recordingBuffer, dataSize);
    
    file.close();
    Serial.println("WAV file saved successfully");
}

// Web server handlers
void handleRoot() {
    String html = "<html><body><h1>OMI ESP32S3 File Server</h1>";
    html += "<p><a href='/list'>List Files</a></p>";
    html += "<p><a href='/status'>Status</a></p>";
    html += "</body></html>";
    server.send(200, "text/html", html);
}

void handleFileList() {
    String json = "[";
    File root = SD.open("/recordings");
    if (root) {
        File file = root.openNextFile();
        bool first = true;
        while (file) {
            if (!first) json += ",";
            json += "{\"name\":\"" + String(file.name()) + "\",\"size\":" + String(file.size()) + "}";
            first = false;
            file = root.openNextFile();
        }
        root.close();
    }
    json += "]";
    server.send(200, "application/json", json);
}

void handleFileDownload() {
    String filename = server.arg("file");
    if (filename.length() == 0) {
        server.send(400, "text/plain", "Missing file parameter");
        return;
    }
    
    String filepath = "/recordings/" + filename;
    if (!SD.exists(filepath)) {
        server.send(404, "text/plain", "File not found");
        return;
    }
    
    File file = SD.open(filepath);
    if (!file) {
        server.send(500, "text/plain", "Failed to open file");
        return;
    }
    
    server.streamFile(file, "audio/wav");
    file.close();
}

void handleStatus() {
    String json = "{";
    json += "\"recording\":" + String(recording ? "true" : "false") + ",";
    json += "\"ble_connected\":" + String(deviceConnected ? "true" : "false") + ",";
    json += "\"display_on\":" + String(displayOn ? "true" : "false") + ",";
    json += "\"sd_card\":" + String(SD.cardType() != CARD_NONE ? "true" : "false") + ",";
    json += "\"free_heap\":" + String(ESP.getFreeHeap()) + ",";
    json += "\"recording_count\":" + String(recordingCounter) + ",";
    json += "\"voice_detected\":" + String(voiceDetected ? "true" : "false") + ",";
    json += "\"last_transcription\":\"" + lastTranscription + "\"";
    json += "}";
    server.send(200, "application/json", json);
}

// Voice Activity Detection - Simple energy-based detection
bool detectVoiceActivity(int16_t* audioData, size_t sampleCount) {
    if (!audioData || sampleCount == 0) return false;
    
    // Calculate RMS energy
    float energy = 0.0;
    for (size_t i = 0; i < sampleCount; i++) {
        energy += (float)audioData[i] * audioData[i];
    }
    energy = sqrt(energy / sampleCount);
    
    return energy > voiceThreshold;
}

// Simple transcription placeholder - sends audio for external processing
void processTranscription() {
    if (!recording || !transcriptionEnabled || recordingIndex == 0) return;
    
    // Detect voice activity in the current recording
    voiceDetected = detectVoiceActivity(recordingBuffer, recordingIndex);
    
    if (voiceDetected && deviceConnected && pTranscriptionCharacteristic) {
        // Send transcription request via BLE
        String transcriptionRequest = "TRANSCRIBE_REQUEST:" + currentRecordingFile + ":" + String(recordingIndex);
        pTranscriptionCharacteristic->setValue(transcriptionRequest.c_str());
        pTranscriptionCharacteristic->notify();
        
        Serial.println("Transcription request sent: " + transcriptionRequest);
    }
}

// Update transcription result (called when receiving transcription from connected device)
void updateTranscription(String transcription) {
    lastTranscription = transcription;
    
    // Save transcription to file
    if (SD.cardType() != CARD_NONE && transcription.length() > 0) {
        String transcriptionFile = currentRecordingFile;
        transcriptionFile.replace(".wav", ".txt");
        
        File file = SD.open(transcriptionFile, FILE_WRITE);
        if (file) {
            file.println("Timestamp: " + String(millis()));
            file.println("Recording: " + currentRecordingFile);
            file.println("Transcription: " + transcription);
            file.close();
            Serial.println("Transcription saved to: " + transcriptionFile);
        }
    }
    
    // Notify via BLE
    if (deviceConnected && pTranscriptionCharacteristic) {
        String result = "TRANSCRIPTION:" + transcription;
        pTranscriptionCharacteristic->setValue(result.c_str());
        pTranscriptionCharacteristic->notify();
    }
}

// Enhanced recording handler with transcription
void handleRecordingWithTranscription() {
    if (!recording || !recordingBuffer) return;
    
    size_t bytesRead = 0;
    esp_err_t result = i2s_read(I2S_NUM_0, audioBuffer, sizeof(audioBuffer), &bytesRead, 10);
    
    if (result == ESP_OK && bytesRead > 0) {
        size_t samplesRead = bytesRead / 2;
        
        // Store in recording buffer
        for (size_t i = 0; i < samplesRead && recordingIndex < recordingBufferSize; i++) {
            recordingBuffer[recordingIndex++] = audioBuffer[i];
        }
        
        // Voice activity detection on current chunk
        if (transcriptionEnabled) {
            bool currentVoiceActivity = detectVoiceActivity(audioBuffer, samplesRead);
            if (currentVoiceActivity && !voiceDetected) {
                voiceDetected = true;
                Serial.println("Voice activity detected!");
            }
        }
        
        // Also send via BLE if connected
        if (deviceConnected) {
            uint32_t timestamp = millis();
            sendAudioViaBLE(audioBuffer, samplesRead, timestamp);
        }
        
        // Check if buffer is full
        if (recordingIndex >= recordingBufferSize) {
            stopRecording();
        }
    }
}