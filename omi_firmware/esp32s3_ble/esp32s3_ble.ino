/*
 * XIAO ESP32S3 Sense - Brutal Honest AI BLE Firmware
 * Simple and reliable BLE audio streaming
 */

#include "BLEDevice.h"
#include "BLEServer.h"
#include "BLEUtils.h"
#include "BLE2902.h"
#include "driver/i2s.h"

// BLE Configuration
#define SERVICE_UUID        "12345678-1234-1234-1234-123456789abc"
#define AUDIO_CHAR_UUID     "12345678-1234-1234-1234-123456789abd"
#define STATUS_CHAR_UUID    "12345678-1234-1234-1234-123456789abe"

// Hardware Configuration
#define LED_PIN LED_BUILTIN
#define SAMPLE_RATE 16000
#define BUFFER_SIZE 512

// I2S Configuration for ESP32S3 Sense built-in microphone
#define I2S_WS 42
#define I2S_SD 41
#define I2S_SCK 2

// Global Variables
BLEServer* pServer = nullptr;
BLECharacteristic* pAudioCharacteristic = nullptr;
BLECharacteristic* pStatusCharacteristic = nullptr;
bool deviceConnected = false;

// Audio buffer
int16_t audioBuffer[BUFFER_SIZE];
uint8_t bleBuffer[BUFFER_SIZE * 2 + 4];

class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
        deviceConnected = true;
        digitalWrite(LED_PIN, HIGH);
        Serial.println("BLE Client connected");
        
        // Send status
        if (pStatusCharacteristic) {
            pStatusCharacteristic->setValue("ESP32S3_CONNECTED");
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
    
    Serial.println("Starting XIAO ESP32S3 Sense - Brutal Honest AI");
    
    // Initialize LED
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);
    
    // Initialize I2S microphone
    initializeI2S();
    
    // Initialize BLE
    initializeBLE();
    
    Serial.println("BLE advertising started - Device ready!");
    
    // Blink LED to show ready
    for (int i = 0; i < 5; i++) {
        digitalWrite(LED_PIN, HIGH);
        delay(200);
        digitalWrite(LED_PIN, LOW);
        delay(200);
    }
}

void loop() {
    // Read audio data
    size_t bytesRead = 0;
    esp_err_t result = i2s_read(I2S_NUM_0, audioBuffer, sizeof(audioBuffer), &bytesRead, portMAX_DELAY);
    
    if (result == ESP_OK && bytesRead > 0 && deviceConnected) {
        uint32_t timestamp = millis();
        sendAudioViaBLE(audioBuffer, bytesRead / 2, timestamp);
    }
    
    // Blink LED when not connected
    if (!deviceConnected) {
        static unsigned long lastBlink = 0;
        if (millis() - lastBlink > 1000) {
            digitalWrite(LED_PIN, !digitalRead(LED_PIN));
            lastBlink = millis();
        }
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
    
    pService->start();
    
    BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->setScanResponse(true);
    pAdvertising->setMinPreferred(0x06);
    pAdvertising->setMinPreferred(0x12);
    pAdvertising->start();
    
    Serial.println("BLE initialized successfully");
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