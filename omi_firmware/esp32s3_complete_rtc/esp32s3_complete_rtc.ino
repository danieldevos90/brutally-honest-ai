/*
 * Brutally Honest AI - Complete Firmware with RTC Clock
 * Features: Voice Recording, RTC Display, Button Control, SD Storage
 * Compatible with XIAO ESP32S3 + Expansion Board
 */

#include <Arduino.h>
#include <U8x8lib.h>
#include <RTClib.h>
#include <Wire.h>
#include <ESP_I2S.h>
#include <SD.h>
#include <SPI.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLE2902.h>
#include <WiFi.h>
#include <time.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// Pin definitions based on XIAO ESP32S3 Expansion Board
#define BUTTON_PIN 2        // Button(D2) - GPIO2 (CORRECTED!)
#define BUZZER_PIN 3        // Buzzer(A3) - GPIO3  
#define LED_PIN 21          // Built-in LED on XIAO ESP32S3 (inverted logic)
#define SD_CS_PIN 21        // SD card chip select - GPIO21

// PDM Microphone pins for ESP32S3 Sense
#define PDM_CLK_PIN 42
#define PDM_DATA_PIN 41

// Battery monitoring
#define BATTERY_ADC_PIN A0      // Battery voltage divider on A0
#define BATTERY_VOLTAGE_DIVIDER 2.0  // Voltage divider ratio (adjust based on hardware)
#define BATTERY_MIN_VOLTAGE 3.0      // Minimum battery voltage (0%)
#define BATTERY_MAX_VOLTAGE 4.2      // Maximum battery voltage (100%)

// Audio configuration
#define SAMPLE_RATE 16000
#define SAMPLE_BITS 16
#define PDM_BUFFER_SIZE 512  // Larger buffer for better quality
#define AUDIO_GAIN 3         // Optimal gain for headroom and clarity

// WiFi and Time configuration
const char* WIFI_SSID = "YourWiFiSSID";        // Change this to your WiFi SSID
const char* WIFI_PASSWORD = "YourWiFiPassword"; // Change this to your WiFi password
const char* NTP_SERVER = "pool.ntp.org";
const long GMT_OFFSET_SEC = 0;                  // GMT offset in seconds (0 for UTC)
const int DAYLIGHT_OFFSET_SEC = 0;              // Daylight saving offset in seconds

// Time sync intervals
const unsigned long TIME_SYNC_INTERVAL = 3600000; // Sync every hour (3600000 ms)
const unsigned long WIFI_TIMEOUT = 10000;         // WiFi connection timeout (10 seconds)

// Initialize components
RTC_PCF8563 rtc;
U8X8_SSD1306_128X64_NONAME_HW_I2C u8x8(/* clock=*/ SCL, /* data=*/ SDA, /* reset=*/ U8X8_PIN_NONE);
I2SClass I2S;

// Recording state
volatile bool isRecording = false;
volatile bool buttonPressed = false;
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 200;
int recordingCount = 0;

// File handling
File currentFile;
bool sdCardPresent = false;
// Track raw PCM bytes written to update WAV header correctly
uint32_t wavDataBytes = 0;
String currentFileName = "";

// BLE setup
#define SERVICE_UUID        "12345678-1234-5678-1234-56789abcdef0"
#define AUDIO_CHAR_UUID     "12345678-1234-5678-1234-56789abcdef1"
#define STATUS_CHAR_UUID    "12345678-1234-5678-1234-56789abcdef2"

BLECharacteristic *pAudioCharacteristic;
BLECharacteristic *pStatusCharacteristic;
bool deviceConnected = false;

// LED control
bool ledState = false;
unsigned long lastLedUpdate = 0;

// Status broadcasting
unsigned long lastStatusBroadcast = 0;
const unsigned long statusBroadcastInterval = 5000; // 5 seconds

// Time synchronization tracking
unsigned long lastTimeSync = 0;
bool wifiConnected = false;
bool timeSynced = false;

// Battery monitoring
float batteryVoltage = 0.0;
int batteryPercentage = 0;
unsigned long lastBatteryRead = 0;
const unsigned long batteryReadInterval = 10000; // Read battery every 10 seconds
int batterySensePin = -1; // Auto-detected ADC pin for VBAT sense, -1 if unavailable
bool batterySenseAvailable = false;

// Button interrupt handler
void IRAM_ATTR handleButtonPress() {
    unsigned long currentTime = millis();
    if (currentTime - lastDebounceTime > debounceDelay) {
        buttonPressed = true;
        lastDebounceTime = currentTime;
        Serial.println("🔘 Button interrupt triggered!");
    }
}

// BLE Server Callbacks
class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
        deviceConnected = true;
        Serial.println("📱 BLE Client Connected!");
        Serial.println("🔗 Connection established successfully");
        
        // Send current status immediately upon connection
        sendStatus();
    }

    void onDisconnect(BLEServer* pServer) {
        deviceConnected = false;
        Serial.println("📱 BLE Client Disconnected!");
        Serial.println("🔄 Restarting advertising...");
        
        // Restart advertising after disconnect
        delay(500);
        BLEDevice::startAdvertising();
        Serial.println("📡 BLE Advertising restarted");
    }
};

// WiFi connection function
bool connectToWiFi() {
    Serial.println("📶 Connecting to WiFi...");
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    
    unsigned long startTime = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - startTime < WIFI_TIMEOUT) {
        delay(500);
        Serial.print(".");
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        wifiConnected = true;
        Serial.println();
        Serial.print("✅ WiFi connected! IP: ");
        Serial.println(WiFi.localIP());
        return true;
    } else {
        wifiConnected = false;
        Serial.println();
        Serial.println("❌ WiFi connection failed");
        return false;
    }
}

// Get current time from WorldTimeAPI (more reliable than NTP for getting timezone info)
bool syncTimeFromInternet() {
    if (!wifiConnected) {
        Serial.println("❌ Cannot sync time - WiFi not connected");
        return false;
    }
    
    HTTPClient http;
    http.begin("http://worldtimeapi.org/api/timezone/Etc/UTC");
    
    int httpResponseCode = http.GET();
    
    if (httpResponseCode == 200) {
        String payload = http.getString();
        Serial.println("📡 Received time data from WorldTimeAPI");
        
        // Parse JSON response
        DynamicJsonDocument doc(1024);
        deserializeJson(doc, payload);
        
        const char* datetime = doc["datetime"];
        if (datetime) {
            // Parse ISO 8601 format: 2024-01-15T12:30:45.123456+00:00
            int year, month, day, hour, minute, second;
            sscanf(datetime, "%d-%d-%dT%d:%d:%d", &year, &month, &day, &hour, &minute, &second);
            
            // Set RTC with the correct time
            rtc.adjust(DateTime(year, month, day, hour, minute, second));
            timeSynced = true;
            lastTimeSync = millis();
            
            Serial.printf("✅ Time synchronized: %04d-%02d-%02d %02d:%02d:%02d\n", 
                         year, month, day, hour, minute, second);
            
            http.end();
            return true;
        }
    } else {
        Serial.print("❌ HTTP request failed, code: ");
        Serial.println(httpResponseCode);
    }
    
    http.end();
    
    // Fallback to NTP if WorldTimeAPI fails
    Serial.println("🔄 Falling back to NTP...");
    return syncTimeFromNTP();
}

// Fallback NTP time synchronization
bool syncTimeFromNTP() {
    if (!wifiConnected) {
        return false;
    }
    
    Serial.println("🕐 Syncing time with NTP server...");
    configTime(GMT_OFFSET_SEC, DAYLIGHT_OFFSET_SEC, NTP_SERVER);
    
    // Wait for time to be set
    int retries = 0;
    while (time(nullptr) < 8 * 3600 * 2 && retries < 10) {
        delay(1000);
        Serial.print(".");
        retries++;
    }
    
    if (retries < 10) {
        time_t now = time(nullptr);
        struct tm* timeinfo = gmtime(&now);
        
        // Set RTC with NTP time
        rtc.adjust(DateTime(timeinfo->tm_year + 1900, timeinfo->tm_mon + 1, timeinfo->tm_mday,
                           timeinfo->tm_hour, timeinfo->tm_min, timeinfo->tm_sec));
        
        timeSynced = true;
        lastTimeSync = millis();
        
        Serial.println();
        Serial.printf("✅ NTP time synchronized: %04d-%02d-%02d %02d:%02d:%02d\n",
                     timeinfo->tm_year + 1900, timeinfo->tm_mon + 1, timeinfo->tm_mday,
                     timeinfo->tm_hour, timeinfo->tm_min, timeinfo->tm_sec);
        return true;
    } else {
        Serial.println();
        Serial.println("❌ NTP synchronization failed");
        return false;
    }
}

// Initialize time synchronization
void initTimeSync() {
    Serial.println("🕐 Initializing time synchronization...");
    
    // Try to connect to WiFi and sync time
    if (connectToWiFi()) {
        if (syncTimeFromInternet()) {
            Serial.println("✅ Time synchronization successful");
        } else {
            Serial.println("⚠️ Time synchronization failed, using RTC time");
        }
        
        // Disconnect WiFi to save power (we'll reconnect when needed)
        WiFi.disconnect();
        wifiConnected = false;
        Serial.println("📶 WiFi disconnected to save power");
    } else {
        Serial.println("⚠️ WiFi connection failed, using RTC time");
    }
}

// Periodic time synchronization
void checkTimeSync() {
    // Only sync if it's been more than TIME_SYNC_INTERVAL since last sync
    if (millis() - lastTimeSync > TIME_SYNC_INTERVAL) {
        Serial.println("🔄 Periodic time synchronization...");
        
        if (connectToWiFi()) {
            syncTimeFromInternet();
            WiFi.disconnect();
            wifiConnected = false;
        }
    }
}

// Battery monitoring functions
int lipoVoltageToPercent(float vbat) {
    if (vbat >= 4.20f) return 100;
    if (vbat >= 4.10f) return 90;
    if (vbat >= 4.00f) return 80;
    if (vbat >= 3.90f) return 70;
    if (vbat >= 3.80f) return 60;
    if (vbat >= 3.70f) return 45;
    if (vbat >= 3.60f) return 30;
    if (vbat >= 3.50f) return 20;
    if (vbat >= 3.40f) return 10;
    if (vbat >= 3.30f) return 5;
    return 0;
}

void readBatteryVoltage() {
    // If VBAT sense not available, keep values neutral
    if (!batterySenseAvailable || batterySensePin < 0) {
        batteryVoltage = 0.0;
        batteryPercentage = 0;
        return;
    }
    // Read pin voltage in millivolts (uses attenuation and calibration)
    int millivolts = analogReadMilliVolts(batterySensePin);
    float voltage = millivolts / 1000.0;
    
    // Apply voltage divider correction
    batteryVoltage = voltage * BATTERY_VOLTAGE_DIVIDER;

    // Use piecewise LiPo curve for percent
    batteryPercentage = lipoVoltageToPercent(batteryVoltage);
    batteryPercentage = constrain(batteryPercentage, 0, 100);
}

String getBatteryStatus() {
    if (batteryVoltage < 3.2) {
        return "LOW";
    } else if (batteryVoltage < 3.6) {
        return "MED";
    } else {
        return "GOOD";
    }
}

void setup() {
    Serial.begin(115200);
    delay(2000);
    
    Serial.println("🚀 Brutally Honest AI - Complete System Starting...");
    Serial.println("================================");
    Serial.print("📱 Device: ESP32S3 with ");
    Serial.print(ESP.getChipModel());
    Serial.print(" (");
    Serial.print(ESP.getChipCores());
    Serial.println(" cores)");
    Serial.print("💾 Flash: ");
    Serial.print(ESP.getFlashChipSize() / (1024 * 1024));
    Serial.println(" MB");
    Serial.print("🧠 RAM: ");
    Serial.print(ESP.getFreeHeap() / 1024);
    Serial.println(" KB free");
    Serial.println("================================");
    
    // Initialize pins
    Serial.println("🔧 Configuring GPIO pins...");
    pinMode(BUTTON_PIN, INPUT_PULLUP);
    pinMode(LED_PIN, OUTPUT);
    pinMode(BUZZER_PIN, OUTPUT);
    
    // Initialize battery monitoring
    Serial.println("🔋 Initializing battery monitoring...");
    analogReadResolution(12);  // Set ADC to 12-bit resolution
    
    // Enable VBAT on A0 with assumed 2:1 divider (hardware required)
    batterySensePin = -1;
    batterySenseAvailable = false;
    Serial.println("ℹ️ VBAT disabled (no sense path). Use 'B' to probe manually.");
    
    readBatteryVoltage();      // Initial battery reading
    Serial.print("  📌 Button: GPIO");
    Serial.println(BUTTON_PIN);
    Serial.print("  💡 LED: GPIO");
    Serial.println(LED_PIN);
    Serial.print("  🔊 Buzzer: GPIO");
    Serial.println(BUZZER_PIN);
    
    // LED off initially (HIGH = OFF for built-in LED)
    digitalWrite(LED_PIN, HIGH);
    
    // Attach button interrupt
    attachInterrupt(digitalPinToInterrupt(BUTTON_PIN), handleButtonPress, FALLING);
    
    // Initialize I2C
    Wire.begin();
    delay(100);
    
    // Initialize OLED
    Serial.println("🔄 Initializing OLED display...");
    u8x8.begin();
    u8x8.setFlipMode(1);
    u8x8.clear();
    
    // Show startup message
    u8x8.setFont(u8x8_font_chroma48medium8_r);
    u8x8.setCursor(0, 0);
    u8x8.print("Brutal Honest");
    u8x8.setCursor(0, 1);
    u8x8.print("AI Starting...");
    
    // Initialize RTC
    Serial.println("🕐 Initializing RTC...");
    if (!rtc.begin()) {
        Serial.println("❌ RTC not found! Using system time");
    } else {
        Serial.println("✅ RTC initialized");
        
        // Check if RTC lost power or time is invalid
        bool needsTimeSync = false;
        if (rtc.lostPower()) {
            Serial.println("⚠️ RTC lost power - time synchronization needed");
            needsTimeSync = true;
        } else {
            // Check if time seems reasonable (after 2020)
            DateTime now = rtc.now();
            if (now.year() < 2020) {
                Serial.println("⚠️ RTC time seems invalid - time synchronization needed");
                needsTimeSync = true;
            } else {
                // RTC time looks valid; mark as synced for UI/status
                timeSynced = true;
                lastTimeSync = millis();
            }
        }
        
        // Initialize time synchronization if needed or always on startup
        initTimeSync();
    }
    
    // Initialize SD card
    Serial.println("💾 Initializing SD card...");
    if (SD.begin(SD_CS_PIN)) {
        sdCardPresent = true;
        Serial.println("✅ SD card initialized");
        
        // Create recordings directory
        if (!SD.exists("/recordings")) {
            SD.mkdir("/recordings");
        }
        
        // Count existing recordings
        File root = SD.open("/recordings");
        if (root) {
            recordingCount = 0;
            while (true) {
                File entry = root.openNextFile();
                if (!entry) break;
                if (!entry.isDirectory() && String(entry.name()).endsWith(".wav")) {
                    recordingCount++;
                }
                entry.close();
            }
            root.close();
            Serial.print("📁 Found ");
            Serial.print(recordingCount);
            Serial.println(" existing recordings");
        }
    } else {
        Serial.println("❌ SD card initialization failed");
    }
    
    // Initialize PDM microphone
    Serial.println("🎤 Initializing PDM microphone...");
    
    // Set PDM pins according to Seeed documentation
    I2S.setPinsPdmRx(PDM_CLK_PIN, PDM_DATA_PIN);
    
    // Initialize I2S with PDM mode for XIAO ESP32S3 Sense
    // For ESP32 3.x: begin(mode, rate, bits, slot_mode)
    if (!I2S.begin(I2S_MODE_PDM_RX, SAMPLE_RATE, I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_MONO)) {
        Serial.println("❌ Failed to initialize I2S for PDM microphone!");
        while (1); // do nothing
    }
    
    Serial.println("✅ PDM Microphone initialized successfully!");
    Serial.println("   - Mode: PDM RX (Mono)");
    Serial.println("   - Sample Rate: 16 kHz");
    Serial.println("   - Bits: 16-bit");
    Serial.println("   - Buffer Size: " + String(PDM_BUFFER_SIZE) + " samples");
    Serial.println("   - Gain: " + String(AUDIO_GAIN) + "x");
    Serial.println("   - CLK Pin: GPIO42");
    Serial.println("   - DATA Pin: GPIO41");
    Serial.println("   - DC Offset: Adaptive removal");
    Serial.println("   - Soft Clipping: Enabled");
    
    // Initialize BLE
    Serial.println("📡 Initializing BLE...");
    initBLE();
    
    // Success feedback
    tone(BUZZER_PIN, 1000, 100);
    delay(150);
    tone(BUZZER_PIN, 1500, 100);
    
    Serial.println("✅ System ready! Press button to start/stop recording.");
    Serial.println("💡 Serial Commands:");
    Serial.println("   - Send 'L' or 'l' to list SD card files");
    Serial.println("   - Send 'S' or 's' to get device status");
    Serial.println("   - Send 'I' or 'i' to get device info");
    Serial.println("   - Send 'T' or 't' to sync time manually");
    Serial.println("🔧 Pin Configuration:");
    Serial.println("   - Button: GPIO2 (D2) ✅ FIXED!");
    Serial.println("   - LED: GPIO21 (built-in)");
    Serial.println("   - Buzzer: GPIO3 (A3)");
    Serial.println("   - SD CS: GPIO21");
    Serial.println("   - I2C SDA: GPIO5, SCL: GPIO4");
    
    // Test button initial state
    Serial.print("🔘 Button initial state: ");
    Serial.println(digitalRead(BUTTON_PIN) ? "HIGH (not pressed)" : "LOW (pressed)");
    
    // Print initial status for USB connection
    Serial.println("📊 Initial Device Status:");
    Serial.print("   - Recording: ");
    Serial.println(isRecording ? "YES" : "NO");
    Serial.print("   - Files on SD: ");
    Serial.println(recordingCount);
    Serial.print("   - SD Card: ");
    Serial.println(sdCardPresent ? "Present" : "Missing");
    Serial.print("   - BLE: ");
    Serial.println("Advertising");
    
    delay(2000);
    u8x8.clear();
}

void initBLE() {
    Serial.println("🔧 Configuring BLE device...");
    
    // Initialize BLE with device name
    BLEDevice::init("BrutallyHonestAI");
    Serial.println("✅ BLE Device initialized as 'BrutallyHonestAI'");
    
    // Set BLE power to maximum for better range
    esp_ble_tx_power_set(ESP_BLE_PWR_TYPE_DEFAULT, ESP_PWR_LVL_P9);
    esp_ble_tx_power_set(ESP_BLE_PWR_TYPE_ADV, ESP_PWR_LVL_P9);
    Serial.println("📡 BLE power set to maximum");
    
    // Create BLE Server
    BLEServer *pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());
    Serial.println("✅ BLE Server created");
    
    // Create BLE Service
    BLEService *pService = pServer->createService(SERVICE_UUID);
    Serial.println("✅ BLE Service created");
    
    // Audio characteristic for streaming
    pAudioCharacteristic = pService->createCharacteristic(
        AUDIO_CHAR_UUID,
        BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
    );
    pAudioCharacteristic->addDescriptor(new BLE2902());
    Serial.println("✅ Audio characteristic created");
    
    // Status characteristic
    pStatusCharacteristic = pService->createCharacteristic(
        STATUS_CHAR_UUID,
        BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
    );
    pStatusCharacteristic->addDescriptor(new BLE2902());
    Serial.println("✅ Status characteristic created");
    
    // Set initial status
    char initialStatus[64];
    sprintf(initialStatus, "Recording: NO, Files: %d", recordingCount);
    pStatusCharacteristic->setValue(initialStatus);
    Serial.print("📊 Initial status set: ");
    Serial.println(initialStatus);
    
    // Start the service
    pService->start();
    Serial.println("✅ BLE Service started");
    
    // Configure advertising with improved parameters
    BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->setScanResponse(true);
    
    // Improved advertising parameters for better connectivity
    pAdvertising->setMinPreferred(0x06);   // 7.5ms minimum interval
    pAdvertising->setMaxPreferred(0x12);   // 22.5ms maximum interval
    
    // Set advertising data
    BLEAdvertisementData advertisementData;
    advertisementData.setName("BrutallyHonestAI");
    advertisementData.setCompleteServices(BLEUUID(SERVICE_UUID));
    advertisementData.setFlags(0x06); // LE General Discoverable Mode + BR/EDR Not Supported
    pAdvertising->setAdvertisementData(advertisementData);
    
    // Set scan response data
    BLEAdvertisementData scanResponseData;
    scanResponseData.setShortName("BrutalAI");
    pAdvertising->setScanResponseData(scanResponseData);
    
    // Start advertising
    BLEDevice::startAdvertising();
    Serial.println("📡 BLE Advertising started with improved parameters!");
    Serial.println("🔍 Device is now discoverable as 'BrutallyHonestAI'");
    Serial.println("📊 Advertising interval: 7.5-22.5ms for better discovery");
    
    // Send initial status notification after delay
    delay(1000);
    sendStatus();
}

void startRecording() {
    if (!sdCardPresent) {
        Serial.println("❌ Cannot record - SD card not available");
        tone(BUZZER_PIN, 500, 300);
        return;
    }
    
    isRecording = true;
    recordingCount++;
    
    // Create filename with timestamp
    DateTime now = rtc.now();
    char filename[50];
    sprintf(filename, "/recordings/rec_%04d%02d%02d_%02d%02d%02d.wav",
            now.year(), now.month(), now.day(),
            now.hour(), now.minute(), now.second());
    currentFileName = String(filename);
    
    currentFile = SD.open(currentFileName, FILE_WRITE);
    if (!currentFile) {
        Serial.println("❌ Failed to create recording file");
        isRecording = false;
        return;
    }
    
    // Reset data counter and write placeholder WAV header
    wavDataBytes = 0;
    writeWAVHeader();
    
    Serial.println("🎤 Recording started: " + currentFileName);
    Serial.println("AUDIO_START"); // Marker for USB streaming
    
    // Short beep
    tone(BUZZER_PIN, 1500, 50);
    
    // Start LED blinking
    lastLedUpdate = millis();
}

void stopRecording() {
    if (!isRecording) return;
    
    isRecording = false;
    
    if (currentFile) {
        // Fix up WAV header sizes before closing
        // RIFF chunk size = 36 + data bytes
        uint32_t riffSize = 36 + wavDataBytes;
        // data chunk size = data bytes
        uint32_t dataSize = wavDataBytes;
        // Seek and write little-endian values
        currentFile.seek(4);
        currentFile.write((uint8_t*)&riffSize, 4);
        currentFile.seek(40);
        currentFile.write((uint8_t*)&dataSize, 4);
        currentFile.flush();
        currentFile.close();
        Serial.println("💾 Recording saved: " + currentFileName);
    }
    
    Serial.println("AUDIO_END"); // Marker for USB streaming
    Serial.println("⏹️ Recording stopped!");
    
    // Short beep
    tone(BUZZER_PIN, 800, 50);
    
    // Turn off LED
    digitalWrite(LED_PIN, HIGH);
}

void writeWAVHeader() {
    // WAV header for 16kHz, 16-bit, mono PCM
    struct WavHeader {
        char riff[4] = {'R','I','F','F'};
        uint32_t fileSize = 0;           // Will be updated later
        char wave[4] = {'W','A','V','E'};
        char fmt[4] = {'f','m','t',' '};
        uint32_t fmtSize = 16;
        uint16_t audioFormat = 1;        // PCM
        uint16_t channels = 1;           // Mono
        uint32_t sampleRate = SAMPLE_RATE;
        uint32_t byteRate = SAMPLE_RATE * 2;  // SampleRate * NumChannels * BitsPerSample/8
        uint16_t blockAlign = 2;         // NumChannels * BitsPerSample/8
        uint16_t bitsPerSample = 16;
        char data[4] = {'d','a','t','a'};
        uint32_t dataSize = 0;           // Will be updated later
    } header;
    
    currentFile.write((uint8_t*)&header, sizeof(header));
}

void updateDisplay() {
    static unsigned long lastDisplayUpdate = 0;
    static bool lastRecordingState = false;
    static int lastRecordingCount = -1;
    static bool lastDeviceConnected = false;
    
    // Only update display every second OR when state changes
    bool stateChanged = (isRecording != lastRecordingState) || 
                       (recordingCount != lastRecordingCount) ||
                       (deviceConnected != lastDeviceConnected);
    
    if (millis() - lastDisplayUpdate < 1000 && !stateChanged) return;
    lastDisplayUpdate = millis();
    
    // Update state tracking
    lastRecordingState = isRecording;
    lastRecordingCount = recordingCount;
    lastDeviceConnected = deviceConnected;
    
    // Only clear display when state changes to reduce flicker
    if (stateChanged) {
        u8x8.clear();
    }
    
    u8x8.setFont(u8x8_font_chroma48medium8_r);
    
    // Title (only update once)
    static bool titleSet = false;
    if (!titleSet || stateChanged) {
        u8x8.setCursor(0, 0);
        u8x8.print("Brutally Honest AI");
        titleSet = true;
    }
    
    // Date and Time using RTC - update every second
    DateTime now = rtc.now();
    
    // Date
    u8x8.setCursor(0, 2);
    char dateStr[12];
    sprintf(dateStr, "%02d/%02d/%04d", now.day(), now.month(), now.year());
    u8x8.print(dateStr);
    
    // Time
    u8x8.setCursor(0, 3);
    char timeStr[10];
    sprintf(timeStr, "%02d:%02d:%02d", now.hour(), now.minute(), now.second());
    u8x8.print(timeStr);
    
    // Status - only update when changed
    if (stateChanged || millis() - lastDisplayUpdate > 5000) {
        u8x8.setCursor(0, 5);
        if (isRecording) {
            u8x8.print("RECORDING...    ");
            u8x8.setCursor(0, 6);
            u8x8.print("Press to stop   ");
        } else {
            u8x8.print("Ready to record ");
            u8x8.setCursor(0, 6);
            u8x8.print("Press button    ");
        }
        
        // Recording count and BLE status
        u8x8.setCursor(0, 7);
        u8x8.print("F:");
        u8x8.print(recordingCount);
        u8x8.print(" BLE:");
        u8x8.print(deviceConnected ? "ON" : "OFF");
        
        // Battery status on line 4 (right side)
        u8x8.setCursor(11, 4);
        u8x8.print("BAT:");
        if (batterySenseAvailable) {
            u8x8.print(batteryPercentage);
            u8x8.print("%");
        } else {
            u8x8.print("--");
            u8x8.print(" ");
        }
        u8x8.print(" T:");
        u8x8.print(timeSynced ? "OK" : "?");
        u8x8.print("  "); // Clear remaining chars
    }
}

void updateLED() {
    if (isRecording) {
        // Blink LED during recording
        unsigned long currentTime = millis();
        if (currentTime - lastLedUpdate > 500) {
            ledState = !ledState;
            digitalWrite(LED_PIN, ledState ? LOW : HIGH); // LOW = ON, HIGH = OFF
            lastLedUpdate = currentTime;
        }
    } else {
        // LED off when not recording
        digitalWrite(LED_PIN, HIGH);
    }
}

void handleRecording() {
    if (!isRecording || !currentFile) return;
    
    // Read audio data with larger buffer for better quality
    int16_t audioBuffer[PDM_BUFFER_SIZE];
    int samplesRead = 0;
    static unsigned long lastRmsPrint = 0;     // debug meter
    static uint32_t rmsAcc = 0;
    static uint32_t rmsCount = 0;
    static int32_t dcOffset = 0;               // DC offset tracker
    static bool firstRun = true;
    
    // Initialize DC offset estimation
    if (firstRun) {
        firstRun = false;
        // Read some samples to estimate DC offset
        int32_t sum = 0;
        int count = 0;
        for (int i = 0; i < 100 && I2S.available(); i++) {
            int sample = I2S.read();
            if (sample != 0 && sample != -1 && sample != 1) {
                sum += sample;
                count++;
            }
        }
        if (count > 0) {
            dcOffset = sum / count;
        }
    }
    
    while (I2S.available() && samplesRead < PDM_BUFFER_SIZE) {
        int sample = I2S.read();
        
        if (sample == 0 || sample == -1 || sample == 1) {
            // Skip invalid samples
            continue;
        }
        
        // Remove DC offset first
        int32_t centered = sample - dcOffset;
        
        // Update DC offset with slow tracking (adaptive)
        dcOffset += (sample - dcOffset) >> 12;
        
        // Apply controlled gain
        int32_t amplified = centered * AUDIO_GAIN;
        
        // Soft clipping to prevent harsh distortion
        if (amplified > 30000) {
            amplified = 30000 + ((amplified - 30000) >> 2);
        } else if (amplified < -30000) {
            amplified = -30000 + ((amplified + 30000) >> 2);
        }
        
        // Final hard clip
        if (amplified > 32767) amplified = 32767;
        if (amplified < -32768) amplified = -32768;
        
        audioBuffer[samplesRead] = (int16_t)amplified;
        
        // Accumulate absolute level for RMS calculation
        rmsAcc += (uint32_t)abs(audioBuffer[samplesRead]);
        rmsCount += 1;
        samplesRead++;
    }
    
    if (samplesRead > 0) {
        int bytesRead = samplesRead * 2;
        
        // Write to SD card
        currentFile.write((uint8_t*)audioBuffer, bytesRead);
        wavDataBytes += bytesRead;
        
        // Send via USB for real-time streaming
        Serial.write((uint8_t*)audioBuffer, bytesRead);
        
        // Send via BLE if connected
        if (deviceConnected && pAudioCharacteristic) {
            // Send in 20-byte chunks for BLE
            for (int i = 0; i < bytesRead; i += 20) {
                int chunkSize = min(20, bytesRead - i);
                pAudioCharacteristic->setValue((uint8_t*)audioBuffer + i, chunkSize);
                pAudioCharacteristic->notify();
            }
        }

        // Debug level print roughly once per second
        unsigned long nowMs = millis();
        if (nowMs - lastRmsPrint > 1000) {
            uint32_t avg = rmsCount ? (rmsAcc / rmsCount) : 0;
            Serial.print("🎚️ Audio level (avg abs): ");
            Serial.println((int)avg);
            rmsAcc = 0;
            rmsCount = 0;
            lastRmsPrint = nowMs;
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
}

// Battery diagnostics: probe multiple analog pins for VBAT sense
void batteryDiagnostics() {
    const int pins[] = {A0, A1, A2, A3, A4, A5};
    const char* names[] = {"A0", "A1", "A2", "A3", "A4", "A5"};
    const size_t numPins = sizeof(pins) / sizeof(pins[0]);
    
    Serial.println("\n🔋 Battery ADC Diagnostics (mV):");
    for (size_t i = 0; i < numPins; ++i) {
        // Configure attenuation for wider range up to ~3.9V on ESP32 ADC input
        analogSetPinAttenuation(pins[i], ADC_11db);
        delay(2);
        int mv = analogReadMilliVolts(pins[i]);
        Serial.print("   ");
        Serial.print(names[i]);
        Serial.print(": ");
        Serial.print(mv);
        Serial.println(" mV");
    }
    
    Serial.println("Hint: The pin reporting ~1800-2100 mV on full charge likely carries VBAT/2.");
}

void listSDCardFiles() {
    Serial.println("\n📁 SD Card Contents:");
    
    if (!sdCardPresent) {
        Serial.println("❌ SD card not present");
        return;
    }
    
    File root = SD.open("/recordings");
    if (!root) {
        Serial.println("❌ Cannot open /recordings directory");
        return;
    }
    
    Serial.println("📂 /recordings/");
    int fileCount = 0;
    unsigned long totalSize = 0;
    
    while (true) {
        File entry = root.openNextFile();
        if (!entry) {
            break;
        }
        
        if (!entry.isDirectory()) {
            Serial.print("   📄 ");
            Serial.print(entry.name());
            Serial.print(" (");
            Serial.print(entry.size());
            Serial.println(" bytes)");
            fileCount++;
            totalSize += entry.size();
        }
        entry.close();
    }
    
    root.close();
    Serial.print("Total files: ");
    Serial.print(fileCount);
    Serial.print(" (");
    Serial.print(totalSize / 1024);
    Serial.println(" KB)");
}

void downloadFile(String filename) {
    Serial.println("📥 DOWNLOAD_START:" + filename);
    
    if (!sdCardPresent) {
        Serial.println("❌ SD card not present");
        Serial.println("📥 DOWNLOAD_ERROR:SD_NOT_PRESENT");
        return;
    }
    
    String fullPath = "/recordings/" + filename;
    File file = SD.open(fullPath, FILE_READ);
    
    if (!file) {
        Serial.println("❌ File not found: " + filename);
        Serial.println("📥 DOWNLOAD_ERROR:FILE_NOT_FOUND");
        return;
    }
    
    Serial.print("📥 DOWNLOAD_SIZE:");
    Serial.println(file.size());
    
    // Send file in chunks
    const int chunkSize = 512;
    uint8_t buffer[chunkSize];
    
    while (file.available()) {
        int bytesRead = file.read(buffer, chunkSize);
        if (bytesRead > 0) {
            Serial.write(buffer, bytesRead);
        }
    }
    
    file.close();
    Serial.println("\n📥 DOWNLOAD_END:" + filename);
}

void deleteFile(String filename) {
    Serial.println("🗑️ DELETE_START:" + filename);
    
    if (!sdCardPresent) {
        Serial.println("❌ SD card not present");
        Serial.println("🗑️ DELETE_ERROR:SD_NOT_PRESENT");
        return;
    }
    
    String fullPath = "/recordings/" + filename;
    
    if (SD.exists(fullPath)) {
        if (SD.remove(fullPath)) {
            Serial.println("✅ File deleted: " + filename);
            Serial.println("🗑️ DELETE_SUCCESS:" + filename);
            
            // Update recording count
            recordingCount = max(0, recordingCount - 1);
        } else {
            Serial.println("❌ Failed to delete: " + filename);
            Serial.println("🗑️ DELETE_ERROR:DELETE_FAILED");
        }
    } else {
        Serial.println("❌ File not found: " + filename);
        Serial.println("🗑️ DELETE_ERROR:FILE_NOT_FOUND");
    }
}

void getFileInfo(String filename) {
    Serial.println("ℹ️ FILE_INFO_START:" + filename);
    
    if (!sdCardPresent) {
        Serial.println("❌ SD card not present");
        Serial.println("ℹ️ FILE_INFO_ERROR:SD_NOT_PRESENT");
        return;
    }
    
    String fullPath = "/recordings/" + filename;
    File file = SD.open(fullPath, FILE_READ);
    
    if (!file) {
        Serial.println("❌ File not found: " + filename);
        Serial.println("ℹ️ FILE_INFO_ERROR:FILE_NOT_FOUND");
        return;
    }
    
    Serial.print("ℹ️ FILE_SIZE:");
    Serial.println(file.size());
    
    // Try to get file timestamp from filename if it follows our format
    if (filename.startsWith("rec_") && filename.length() >= 19) {
        String dateTime = filename.substring(4, 19); // Extract YYYYMMDD_HHMMSS
        Serial.print("ℹ️ FILE_TIMESTAMP:");
        Serial.println(dateTime);
    }
    
    // Check if it's a valid WAV file
    uint8_t header[12];
    if (file.read(header, 12) == 12) {
        if (header[0] == 'R' && header[1] == 'I' && header[2] == 'F' && header[3] == 'F' &&
            header[8] == 'W' && header[9] == 'A' && header[10] == 'V' && header[11] == 'E') {
            Serial.println("ℹ️ FILE_TYPE:WAV");
            Serial.println("ℹ️ FILE_VALID:YES");
        } else {
            Serial.println("ℹ️ FILE_TYPE:UNKNOWN");
            Serial.println("ℹ️ FILE_VALID:NO");
        }
    }
    
    file.close();
    Serial.println("ℹ️ FILE_INFO_END:" + filename);
}

void loop() {
    // Check for serial commands
    if (Serial.available()) {
        String command = Serial.readStringUntil('\n');
        command.trim();
        
        if (command.length() == 0) return;
        
        char cmd = command.charAt(0);
        
        switch (cmd) {
            case 'L':
            case 'l':
                Serial.println("📋 Listing SD card files...");
                listSDCardFiles();
                break;
                
            case 'S':
            case 's':
                Serial.println("📊 Device Status:");
                Serial.print("   - Recording: ");
                Serial.println(isRecording ? "YES" : "NO");
                Serial.print("   - Files: ");
                Serial.println(recordingCount);
                Serial.print("   - SD Card: ");
                Serial.println(sdCardPresent ? "Present" : "Missing");
                Serial.print("   - BLE Connected: ");
                Serial.println(deviceConnected ? "YES" : "NO");
                Serial.print("   - Battery: ");
                Serial.print(batteryVoltage, 2);
                Serial.print("V (");
                Serial.print(batteryPercentage);
                Serial.print("% - ");
                Serial.print(getBatteryStatus());
                Serial.println(")");
                Serial.print("   - Free RAM: ");
                Serial.print(ESP.getFreeHeap() / 1024);
                Serial.println(" KB");
                break;
                
            case 'I':
            case 'i':
                Serial.println("ℹ️  Device Information:");
                Serial.print("   - Model: ");
                Serial.println(ESP.getChipModel());
                Serial.print("   - Cores: ");
                Serial.println(ESP.getChipCores());
                Serial.print("   - Flash: ");
                Serial.print(ESP.getFlashChipSize() / (1024 * 1024));
                Serial.println(" MB");
                Serial.print("   - MAC Address: ");
                Serial.println(WiFi.macAddress());
                Serial.print("   - Uptime: ");
                Serial.print(millis() / 1000);
                Serial.println(" seconds");
                Serial.print("   - Time Synced: ");
                Serial.println(timeSynced ? "YES" : "NO");
                if (timeSynced) {
                    Serial.print("   - Last Sync: ");
                    Serial.print((millis() - lastTimeSync) / 1000);
                    Serial.println(" seconds ago");
                }
                break;
                
            case 'T':
            case 't':
                Serial.println("🕐 Manual time synchronization...");
                if (connectToWiFi()) {
                    if (syncTimeFromInternet()) {
                        Serial.println("✅ Time synchronization successful");
                        DateTime now = rtc.now();
                        Serial.printf("📅 Current time: %04d-%02d-%02d %02d:%02d:%02d\n",
                                     now.year(), now.month(), now.day(),
                                     now.hour(), now.minute(), now.second());
                    } else {
                        Serial.println("❌ Time synchronization failed");
                    }
                    WiFi.disconnect();
                    wifiConnected = false;
                } else {
                    Serial.println("❌ WiFi connection failed");
                }
                break;
                
            case 'D':
            case 'd':
                // Download file: D:filename.wav
                if (command.length() > 2 && command.charAt(1) == ':') {
                    String filename = command.substring(2);
                    Serial.println("📥 Download request: " + filename);
                    downloadFile(filename);
                } else {
                    Serial.println("❓ Usage: D:filename.wav");
                }
                break;
                
            case 'R':
            case 'r':
                // Delete (Remove) file: R:filename.wav
                if (command.length() > 2 && command.charAt(1) == ':') {
                    String filename = command.substring(2);
                    Serial.println("🗑️ Delete request: " + filename);
                    deleteFile(filename);
                } else {
                    Serial.println("❓ Usage: R:filename.wav");
                }
                break;
                
            case 'F':
            case 'f':
                // File info: F:filename.wav
                if (command.length() > 2 && command.charAt(1) == ':') {
                    String filename = command.substring(2);
                    Serial.println("ℹ️ File info request: " + filename);
                    getFileInfo(filename);
                } else {
                    Serial.println("❓ Usage: F:filename.wav");
                }
                break;
            
            case 'B':
            case 'b':
                Serial.println("🔬 Running battery diagnostics...");
                batteryDiagnostics();
                break;
                
            default:
                Serial.println("❓ Unknown command. Available commands:");
                Serial.println("   L - List SD card files");
                Serial.println("   S - Device status");
                Serial.println("   I - Device info");
                Serial.println("   T - Sync time manually");
                Serial.println("   D:filename.wav - Download file");
                Serial.println("   R:filename.wav - Delete file");
                Serial.println("   F:filename.wav - Get file info");
                break;
        }
    }
    
    // Handle button press with additional polling for reliability
    static bool lastButtonState = HIGH;
    bool currentButtonState = digitalRead(BUTTON_PIN);
    
    // Check for button press via interrupt OR polling
    if (buttonPressed || (lastButtonState == HIGH && currentButtonState == LOW)) {
        buttonPressed = false;
        
        // Additional debouncing
        delay(50);
        if (digitalRead(BUTTON_PIN) == LOW) {
            Serial.println("🎯 Button press confirmed!");
            
            if (isRecording) {
                Serial.println("⏹️ Stopping recording...");
                stopRecording();
            } else {
                Serial.println("🎤 Starting recording...");
                startRecording();
            }
            
            // Wait for button release
            while (digitalRead(BUTTON_PIN) == LOW) {
                delay(10);
            }
            delay(100); // Additional debounce after release
        }
    }
    
    lastButtonState = currentButtonState;
    
    // Handle recording
    handleRecording();
    
    // Update battery monitoring
    if (millis() - lastBatteryRead >= batteryReadInterval) {
        readBatteryVoltage();
        lastBatteryRead = millis();
    }
    
    // Update display
    updateDisplay();
    
    // Update LED
    updateLED();
    
    // Send periodic status updates and BLE health check
    static unsigned long lastStatusUpdate = 0;
    static unsigned long lastBLECheck = 0;
    
    if (millis() - lastStatusUpdate > 5000) {
        sendStatus();
        lastStatusUpdate = millis();
        
        // Also print status to serial for USB connectivity
        if (!isRecording) { // Don't spam during recording
            Serial.print("📊 Periodic Status: Recording=");
            Serial.print(isRecording ? "YES" : "NO");
            Serial.print(", Files=");
            Serial.print(recordingCount);
            Serial.print(", BLE=");
            Serial.print(deviceConnected ? "Connected" : "Advertising");
            Serial.print(", RAM=");
            Serial.print(ESP.getFreeHeap() / 1024);
            Serial.println("KB");
        }
    }
    
    // BLE health check and restart advertising if needed
    if (millis() - lastBLECheck > 30000) { // Every 30 seconds
        lastBLECheck = millis();
        
        if (!deviceConnected) {
            Serial.println("🔄 BLE Health Check: Restarting advertising...");
            BLEDevice::startAdvertising();
            Serial.println("📡 BLE Advertising refreshed");
        } else {
            Serial.println("✅ BLE Health Check: Client connected");
        }
    }
    
    // Periodic time synchronization check
    checkTimeSync();
    
    // Small delay to prevent overwhelming the system
    delay(10);
}
