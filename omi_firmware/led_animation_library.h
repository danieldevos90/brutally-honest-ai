/*
 * LED Animation Library for Brutally Honest AI
 * Provides cool visual feedback for all device states
 */

#ifndef LED_ANIMATIONS_H
#define LED_ANIMATIONS_H

#include <Arduino.h>

class LEDAnimator {
private:
    int ledPin;
    int ledChannel;
    unsigned long lastUpdate;
    int animationStep;
    int brightness;
    bool direction;
    
public:
    enum AnimationState {
        IDLE,
        RECORDING,
        PROCESSING,
        UPLOADING,
        SUCCESS,
        ERROR,
        CONNECTING,
        LISTENING,
        BRUTAL_FEEDBACK,
        LOW_BATTERY
    };
    
    AnimationState currentState;
    
    LEDAnimator(int pin) {
        ledPin = pin;
        ledChannel = 0;
        lastUpdate = 0;
        animationStep = 0;
        brightness = 0;
        direction = true;
        currentState = IDLE;
    }
    
    void begin() {
        // Setup PWM for smooth animations
        ledcSetup(ledChannel, 5000, 8);  // 5kHz, 8-bit resolution
        ledcAttachPin(ledPin, ledChannel);
        
        // Run startup animation
        startupAnimation();
    }
    
    void setState(AnimationState state) {
        if (currentState != state) {
            currentState = state;
            animationStep = 0;
            Serial.printf("LED State: %d\n", state);
        }
    }
    
    void update() {
        switch (currentState) {
            case IDLE:
                breathingEffect();
                break;
            case RECORDING:
                recordingPulse();
                break;
            case PROCESSING:
                processingSpinner();
                break;
            case UPLOADING:
                uploadingBlink();
                break;
            case SUCCESS:
                successFlash();
                break;
            case ERROR:
                errorFlash();
                break;
            case CONNECTING:
                connectingPulse();
                break;
            case LISTENING:
                listeningWave();
                break;
            case BRUTAL_FEEDBACK:
                brutalFeedbackEffect();
                break;
            case LOW_BATTERY:
                lowBatteryWarning();
                break;
        }
    }
    
private:
    void breathingEffect() {
        // Gentle breathing for idle state
        if (millis() - lastUpdate > 20) {
            lastUpdate = millis();
            
            if (direction) {
                brightness += 1;
                if (brightness >= 80) direction = false;
            } else {
                brightness -= 1;
                if (brightness <= 0) {
                    direction = true;
                    delay(300);  // Pause at bottom
                }
            }
            ledcWrite(ledChannel, brightness);
        }
    }
    
    void recordingPulse() {
        // Fast red pulsing for recording
        if (millis() - lastUpdate > 8) {
            lastUpdate = millis();
            
            if (direction) {
                brightness += 10;
                if (brightness >= 255) direction = false;
            } else {
                brightness -= 10;
                if (brightness <= 50) direction = true;
            }
            ledcWrite(ledChannel, brightness);
        }
    }
    
    void processingSpinner() {
        // Spinning effect using sine wave
        if (millis() - lastUpdate > 30) {
            lastUpdate = millis();
            animationStep++;
            
            int brightness = (sin(animationStep * 0.1) + 1) * 127;
            ledcWrite(ledChannel, brightness);
        }
    }
    
    void uploadingBlink() {
        // Fast blinking
        if (millis() - lastUpdate > 100) {
            lastUpdate = millis();
            brightness = (brightness == 0) ? 255 : 0;
            ledcWrite(ledChannel, brightness);
        }
    }
    
    void successFlash() {
        // Three bright flashes then back to idle
        if (animationStep < 6 && millis() - lastUpdate > 150) {
            lastUpdate = millis();
            ledcWrite(ledChannel, (animationStep % 2) ? 255 : 0);
            animationStep++;
        } else if (animationStep >= 6) {
            setState(IDLE);
        }
    }
    
    void errorFlash() {
        // Rapid red flashing
        if (millis() - lastUpdate > 50) {
            lastUpdate = millis();
            brightness = (brightness == 0) ? 255 : 0;
            ledcWrite(ledChannel, brightness);
        }
    }
    
    void connectingPulse() {
        // Double pulse pattern
        static int pulsePhase = 0;
        
        if (millis() - lastUpdate > 200) {
            lastUpdate = millis();
            
            switch (pulsePhase) {
                case 0:
                case 2:
                    ledcWrite(ledChannel, 255);
                    break;
                case 1:
                case 3:
                    ledcWrite(ledChannel, 0);
                    break;
                case 4:
                    ledcWrite(ledChannel, 0);
                    pulsePhase = -1;  // Reset
                    delay(600);
                    break;
            }
            pulsePhase++;
        }
    }
    
    void listeningWave() {
        // Smooth wave effect
        if (millis() - lastUpdate > 40) {
            lastUpdate = millis();
            animationStep++;
            
            int brightness = (sin(animationStep * 0.05) + 1) * 80 + 20;
            ledcWrite(ledChannel, brightness);
        }
    }
    
    void brutalFeedbackEffect() {
        // Dramatic effect for brutal feedback
        if (animationStep == 0) {
            // Initial dramatic pause
            ledcWrite(ledChannel, 0);
            delay(500);
            animationStep = 1;
        } else if (animationStep <= 6 && millis() - lastUpdate > 100) {
            // Sharp flashes
            lastUpdate = millis();
            ledcWrite(ledChannel, (animationStep % 2) ? 255 : 0);
            animationStep++;
        } else if (animationStep > 6) {
            setState(LISTENING);
        }
    }
    
    void lowBatteryWarning() {
        // Slow blinking for low battery
        if (millis() - lastUpdate > 1000) {
            lastUpdate = millis();
            brightness = (brightness == 0) ? 100 : 0;
            ledcWrite(ledChannel, brightness);
        }
    }
    
    void startupAnimation() {
        // Cool startup sequence
        Serial.println("🎨 LED Startup Animation");
        
        // Fade in and out 3 times
        for (int cycle = 0; cycle < 3; cycle++) {
            for (int b = 0; b <= 255; b += 5) {
                ledcWrite(ledChannel, b);
                delay(3);
            }
            for (int b = 255; b >= 0; b -= 5) {
                ledcWrite(ledChannel, b);
                delay(3);
            }
        }
        
        // Quick flashes
        for (int i = 0; i < 5; i++) {
            ledcWrite(ledChannel, 255);
            delay(50);
            ledcWrite(ledChannel, 0);
            delay(50);
        }
        
        // End at idle brightness
        ledcWrite(ledChannel, 0);
    }
};

// Convenience functions for specific events
void showWiFiConnected(LEDAnimator& led) {
    // Smooth wave animation
    for (int i = 0; i < 2; i++) {
        for (int b = 0; b <= 255; b += 3) {
            ledcWrite(0, b);
            delay(2);
        }
        for (int b = 255; b >= 0; b -= 3) {
            ledcWrite(0, b);
            delay(2);
        }
    }
}

void showButtonPress(LEDAnimator& led) {
    // Quick flash for button feedback
    ledcWrite(0, 255);
    delay(50);
    ledcWrite(0, 0);
}

#endif // LED_ANIMATIONS_H
