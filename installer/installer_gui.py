#!/usr/bin/env python3
"""
Brutally Honest AI - Visual Installer
Cross-platform GUI installer with progress tracking
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import subprocess
import sys
import os
import platform
import time
import json
import serial.tools.list_ports
from pathlib import Path
import webbrowser

class BrutallyHonestInstaller:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Brutally Honest AI - Installer")
        self.root.geometry("800x600")
        self.root.resizable(False, False)
        
        # Set icon based on platform
        if platform.system() == "Darwin":
            # macOS specific settings
            self.root.createcommand('tk::mac::Quit', self.quit_app)
        
        # Variables
        self.current_step = 0
        self.total_steps = 8
        self.device_port = None
        self.firmware_choice = tk.IntVar(value=1)
        
        # Color scheme
        self.bg_color = "#1a1a1a"
        self.fg_color = "#ffffff"
        self.accent_color = "#00ff88"
        self.error_color = "#ff4444"
        self.warning_color = "#ffaa00"
        
        self.root.configure(bg=self.bg_color)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Create the visual installer interface"""
        # Header with logo
        header_frame = tk.Frame(self.root, bg=self.bg_color)
        header_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # ASCII Art Logo
        logo_text = """
╔══════════════════════════════════════════════════════════════╗
║      ____             _        _ _         _   _             ║
║     |  _ \           | |      | | |       | | | |            ║
║     | |_) |_ __ _   _| |_ __ _| | |_   _  | |_| | ___  _ __  ║
║     |  _ <| '__| | | | __/ _` | | | | | | |  _  |/ _ \| '_ \ ║
║     | |_) | |  | |_| | || (_| | | | |_| | | | | | (_) | | | |║
║     |____/|_|   \__,_|\__\__,_|_|_|\__, | |_| |_|\___/|_| |_|║
║                                      __/ |                    ║
║                   AI INSTALLER      |___/                     ║
╚══════════════════════════════════════════════════════════════╝
        """
        
        logo_label = tk.Label(header_frame, text=logo_text, 
                            font=("Courier", 10), 
                            fg=self.accent_color, 
                            bg=self.bg_color)
        logo_label.pack()
        
        # Progress section
        progress_frame = tk.Frame(self.root, bg=self.bg_color)
        progress_frame.pack(fill=tk.X, padx=40, pady=10)
        
        self.progress_label = tk.Label(progress_frame, 
                                     text="Ready to install", 
                                     font=("Arial", 14, "bold"),
                                     fg=self.fg_color, 
                                     bg=self.bg_color)
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(progress_frame, 
                                          length=700, 
                                          mode='determinate',
                                          style="Custom.Horizontal.TProgressbar")
        self.progress_bar.pack(pady=10)
        
        # Style the progress bar
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Custom.Horizontal.TProgressbar",
                       background=self.accent_color,
                       troughcolor=self.bg_color,
                       bordercolor=self.bg_color,
                       lightcolor=self.accent_color,
                       darkcolor=self.accent_color)
        
        # Main content area
        self.content_frame = tk.Frame(self.root, bg=self.bg_color)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)
        
        # Log output area
        log_frame = tk.Frame(self.root, bg=self.bg_color)
        log_frame.pack(fill=tk.X, padx=40, pady=(0, 20))
        
        log_label = tk.Label(log_frame, text="Installation Log:", 
                           font=("Arial", 10), 
                           fg=self.fg_color, 
                           bg=self.bg_color)
        log_label.pack(anchor=tk.W)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, 
                                                height=8, 
                                                bg="#2a2a2a", 
                                                fg=self.fg_color,
                                                font=("Courier", 9))
        self.log_text.pack(fill=tk.X)
        
        # Button area
        button_frame = tk.Frame(self.root, bg=self.bg_color)
        button_frame.pack(fill=tk.X, padx=40, pady=(0, 20))
        
        self.install_button = tk.Button(button_frame, 
                                      text="Start Installation", 
                                      command=self.start_installation,
                                      bg=self.accent_color, 
                                      fg=self.bg_color,
                                      font=("Arial", 12, "bold"),
                                      padx=30, 
                                      pady=10,
                                      relief=tk.FLAT,
                                      cursor="hand2")
        self.install_button.pack(side=tk.RIGHT)
        
        self.cancel_button = tk.Button(button_frame, 
                                     text="Cancel", 
                                     command=self.quit_app,
                                     bg="#444444", 
                                     fg=self.fg_color,
                                     font=("Arial", 12),
                                     padx=20, 
                                     pady=10,
                                     relief=tk.FLAT,
                                     cursor="hand2")
        self.cancel_button.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Show welcome screen
        self.show_welcome_screen()
        
    def show_welcome_screen(self):
        """Display the welcome screen with hardware requirements"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        welcome_frame = tk.Frame(self.content_frame, bg=self.bg_color)
        welcome_frame.pack(expand=True)
        
        title = tk.Label(welcome_frame, 
                        text="Welcome to Brutally Honest AI", 
                        font=("Arial", 20, "bold"),
                        fg=self.accent_color, 
                        bg=self.bg_color)
        title.pack(pady=20)
        
        subtitle = tk.Label(welcome_frame, 
                          text="Transform your XIAO ESP32S3 into an AI-powered voice recorder",
                          font=("Arial", 12),
                          fg=self.fg_color, 
                          bg=self.bg_color)
        subtitle.pack()
        
        # Requirements
        req_frame = tk.Frame(welcome_frame, bg="#2a2a2a", relief=tk.RIDGE, bd=2)
        req_frame.pack(pady=30, padx=50, fill=tk.BOTH)
        
        req_title = tk.Label(req_frame, 
                           text="✓ Hardware Requirements:", 
                           font=("Arial", 12, "bold"),
                           fg=self.accent_color, 
                           bg="#2a2a2a")
        req_title.pack(anchor=tk.W, padx=20, pady=(10, 5))
        
        requirements = [
            "• Seeed Studio XIAO ESP32S3 Sense",
            "• XIAO Expansion Board (with OLED display)",
            "• Micro SD Card (FAT32 formatted)",
            "• USB-C Data Cable (not charging-only)"
        ]
        
        for req in requirements:
            label = tk.Label(req_frame, 
                           text=req, 
                           font=("Arial", 11),
                           fg=self.fg_color, 
                           bg="#2a2a2a")
            label.pack(anchor=tk.W, padx=40)
            
        # Features
        feat_title = tk.Label(req_frame, 
                            text="✨ Features:", 
                            font=("Arial", 12, "bold"),
                            fg=self.accent_color, 
                            bg="#2a2a2a")
        feat_title.pack(anchor=tk.W, padx=20, pady=(15, 5))
        
        features = [
            "• Voice recording with button toggle",
            "• 'Brutal Honest Query' OLED display",
            "• Automatic Whisper AI transcription",
            "• WiFi & Bluetooth connectivity",
            "• Web interface for management"
        ]
        
        for feat in features:
            label = tk.Label(req_frame, 
                           text=feat, 
                           font=("Arial", 11),
                           fg=self.fg_color, 
                           bg="#2a2a2a")
            label.pack(anchor=tk.W, padx=40, pady=(0, 5))
            
    def log(self, message, level="info"):
        """Add message to log with color coding"""
        timestamp = time.strftime("%H:%M:%S")
        
        # Insert with tag for coloring
        self.log_text.insert(tk.END, f"[{timestamp}] ")
        
        if level == "error":
            self.log_text.insert(tk.END, message + "\n", "error")
            self.log_text.tag_config("error", foreground=self.error_color)
        elif level == "warning":
            self.log_text.insert(tk.END, message + "\n", "warning")
            self.log_text.tag_config("warning", foreground=self.warning_color)
        elif level == "success":
            self.log_text.insert(tk.END, message + "\n", "success")
            self.log_text.tag_config("success", foreground=self.accent_color)
        else:
            self.log_text.insert(tk.END, message + "\n")
            
        self.log_text.see(tk.END)
        self.root.update()
        
    def update_progress(self, step, message):
        """Update progress bar and status"""
        self.current_step = step
        progress = (step / self.total_steps) * 100
        self.progress_bar['value'] = progress
        self.progress_label.config(text=message)
        self.root.update()
        
    def run_command(self, command, shell=True):
        """Run a command and capture output"""
        try:
            if isinstance(command, list):
                result = subprocess.run(command, 
                                      capture_output=True, 
                                      text=True, 
                                      shell=False)
            else:
                result = subprocess.run(command, 
                                      capture_output=True, 
                                      text=True, 
                                      shell=shell)
            
            if result.returncode != 0:
                self.log(f"Command failed: {result.stderr}", "error")
                return False, result.stderr
            return True, result.stdout
        except Exception as e:
            self.log(f"Error running command: {str(e)}", "error")
            return False, str(e)
            
    def check_dependencies(self):
        """Check and install required dependencies"""
        self.update_progress(1, "Checking dependencies...")
        self.log("Checking system dependencies...")
        
        # Check Python
        self.log("✓ Python 3 found", "success")
        
        # Check Arduino CLI
        success, _ = self.run_command("arduino-cli version")
        if not success:
            self.log("Arduino CLI not found. Please install from arduino.cc", "error")
            return False
        self.log("✓ Arduino CLI found", "success")
        
        # Setup Arduino
        self.log("Setting up Arduino environment...")
        self.run_command("arduino-cli config init")
        self.run_command("arduino-cli config add board_manager.additional_urls https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json")
        self.run_command("arduino-cli core update-index")
        
        # Install ESP32 core
        success, output = self.run_command("arduino-cli core list")
        if "esp32:esp32" not in output:
            self.log("Installing ESP32 core (this may take a few minutes)...")
            success, _ = self.run_command("arduino-cli core install esp32:esp32")
            if success:
                self.log("✓ ESP32 core installed", "success")
        else:
            self.log("✓ ESP32 core already installed", "success")
            
        # Install libraries
        libraries = ["U8g2", "ArduinoJson"]
        for lib in libraries:
            self.log(f"Installing {lib} library...")
            self.run_command(f"arduino-cli lib install \"{lib}\"")
            
        return True
        
    def show_device_selection(self):
        """Show device selection screen"""
        self.update_progress(2, "Select your device...")
        
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        device_frame = tk.Frame(self.content_frame, bg=self.bg_color)
        device_frame.pack(expand=True)
        
        title = tk.Label(device_frame, 
                        text="Connect Your Device", 
                        font=("Arial", 18, "bold"),
                        fg=self.accent_color, 
                        bg=self.bg_color)
        title.pack(pady=20)
        
        instructions = tk.Label(device_frame, 
                              text="Please connect your XIAO ESP32S3 via USB-C cable",
                              font=("Arial", 12),
                              fg=self.fg_color, 
                              bg=self.bg_color)
        instructions.pack()
        
        # Device list
        list_frame = tk.Frame(device_frame, bg="#2a2a2a", relief=tk.RIDGE, bd=2)
        list_frame.pack(pady=20, padx=50, fill=tk.BOTH)
        
        list_title = tk.Label(list_frame, 
                            text="Available Devices:", 
                            font=("Arial", 12, "bold"),
                            fg=self.accent_color, 
                            bg="#2a2a2a")
        list_title.pack(anchor=tk.W, padx=20, pady=10)
        
        self.device_var = tk.StringVar()
        
        # Scan for devices
        ports = serial.tools.list_ports.comports()
        esp32_ports = []
        
        for port in ports:
            if any(x in port.description.lower() for x in ['esp32', 'cp210', 'ch340', 'ch9102']):
                esp32_ports.append(port)
                
        if esp32_ports:
            for port in esp32_ports:
                rb = tk.Radiobutton(list_frame, 
                                  text=f"{port.device} - {port.description}",
                                  variable=self.device_var, 
                                  value=port.device,
                                  font=("Arial", 11),
                                  fg=self.fg_color, 
                                  bg="#2a2a2a",
                                  selectcolor="#2a2a2a",
                                  activebackground="#2a2a2a",
                                  activeforeground=self.accent_color)
                rb.pack(anchor=tk.W, padx=40, pady=5)
                
            self.device_var.set(esp32_ports[0].device)  # Select first by default
            self.log(f"Found {len(esp32_ports)} ESP32 device(s)", "success")
        else:
            no_device = tk.Label(list_frame, 
                               text="No ESP32 devices found. Please check connection.",
                               font=("Arial", 11),
                               fg=self.error_color, 
                               bg="#2a2a2a")
            no_device.pack(padx=40, pady=20)
            
            # Boot mode instructions
            boot_frame = tk.Frame(device_frame, bg="#2a2a2a", relief=tk.RIDGE, bd=2)
            boot_frame.pack(pady=10, padx=50, fill=tk.BOTH)
            
            boot_title = tk.Label(boot_frame, 
                                text="💡 Try BOOT Mode:", 
                                font=("Arial", 12, "bold"),
                                fg=self.warning_color, 
                                bg="#2a2a2a")
            boot_title.pack(anchor=tk.W, padx=20, pady=10)
            
            boot_steps = [
                "1. Hold the BOOT button on ESP32S3",
                "2. While holding BOOT, press and release RESET",
                "3. Keep holding BOOT for 2-3 seconds",
                "4. Release BOOT button",
                "5. Click 'Refresh Devices' below"
            ]
            
            for step in boot_steps:
                label = tk.Label(boot_frame, 
                               text=step, 
                               font=("Arial", 11),
                               fg=self.fg_color, 
                               bg="#2a2a2a")
                label.pack(anchor=tk.W, padx=40, pady=2)
                
        # Refresh button
        refresh_btn = tk.Button(device_frame, 
                              text="🔄 Refresh Devices", 
                              command=self.show_device_selection,
                              bg="#444444", 
                              fg=self.fg_color,
                              font=("Arial", 11),
                              padx=20, 
                              pady=8,
                              relief=tk.FLAT,
                              cursor="hand2")
        refresh_btn.pack(pady=10)
        
        if esp32_ports:
            # Continue button
            continue_btn = tk.Button(device_frame, 
                                   text="Continue →", 
                                   command=self.confirm_device,
                                   bg=self.accent_color, 
                                   fg=self.bg_color,
                                   font=("Arial", 12, "bold"),
                                   padx=30, 
                                   pady=10,
                                   relief=tk.FLAT,
                                   cursor="hand2")
            continue_btn.pack(pady=20)
            
    def confirm_device(self):
        """Confirm device selection and proceed"""
        self.device_port = self.device_var.get()
        self.log(f"Selected device: {self.device_port}", "success")
        self.show_firmware_selection()
        
    def show_firmware_selection(self):
        """Show firmware selection screen"""
        self.update_progress(3, "Select firmware version...")
        
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        firmware_frame = tk.Frame(self.content_frame, bg=self.bg_color)
        firmware_frame.pack(expand=True)
        
        title = tk.Label(firmware_frame, 
                        text="Choose Firmware Version", 
                        font=("Arial", 18, "bold"),
                        fg=self.accent_color, 
                        bg=self.bg_color)
        title.pack(pady=20)
        
        # Firmware options
        options = [
            {
                "value": 1,
                "title": "🚀 Full Firmware (Recommended)",
                "desc": "Complete system with recording, WiFi, BLE, and web interface",
                "features": ["Voice recording", "WiFi sync", "Web dashboard", "AI transcription"]
            },
            {
                "value": 2,
                "title": "🧪 Toggle Recording Test",
                "desc": "Simple test firmware for verifying hardware",
                "features": ["Basic recording", "Button testing", "Display test"]
            },
            {
                "value": 3,
                "title": "🔧 OLED Display Test",
                "desc": "Test firmware for troubleshooting display issues",
                "features": ["Display diagnostics", "Pin detection", "Basic functionality"]
            }
        ]
        
        for opt in options:
            # Option frame
            opt_frame = tk.Frame(firmware_frame, bg="#2a2a2a", relief=tk.RIDGE, bd=2)
            opt_frame.pack(pady=10, padx=50, fill=tk.X)
            
            # Radio button and title
            title_frame = tk.Frame(opt_frame, bg="#2a2a2a")
            title_frame.pack(fill=tk.X, padx=20, pady=(10, 5))
            
            rb = tk.Radiobutton(title_frame, 
                              text=opt["title"],
                              variable=self.firmware_choice, 
                              value=opt["value"],
                              font=("Arial", 14, "bold"),
                              fg=self.fg_color, 
                              bg="#2a2a2a",
                              selectcolor="#2a2a2a",
                              activebackground="#2a2a2a",
                              activeforeground=self.accent_color)
            rb.pack(side=tk.LEFT)
            
            # Description
            desc_label = tk.Label(opt_frame, 
                                text=opt["desc"], 
                                font=("Arial", 10),
                                fg="#cccccc", 
                                bg="#2a2a2a",
                                wraplength=600)
            desc_label.pack(anchor=tk.W, padx=60, pady=(0, 5))
            
            # Features
            for feature in opt["features"]:
                feat_label = tk.Label(opt_frame, 
                                    text=f"  ✓ {feature}", 
                                    font=("Arial", 9),
                                    fg=self.accent_color, 
                                    bg="#2a2a2a")
                feat_label.pack(anchor=tk.W, padx=80, pady=1)
                
        # Continue button
        continue_btn = tk.Button(firmware_frame, 
                               text="Install Selected Firmware →", 
                               command=self.install_firmware,
                               bg=self.accent_color, 
                               fg=self.bg_color,
                               font=("Arial", 12, "bold"),
                               padx=30, 
                               pady=10,
                               relief=tk.FLAT,
                               cursor="hand2")
        continue_btn.pack(pady=30)
        
    def install_firmware(self):
        """Start the firmware installation process"""
        self.install_button.config(state=tk.DISABLED)
        
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        # Show installation progress
        install_frame = tk.Frame(self.content_frame, bg=self.bg_color)
        install_frame.pack(expand=True)
        
        # Animated installation display
        self.status_label = tk.Label(install_frame, 
                                   text="Installing Firmware...", 
                                   font=("Arial", 16, "bold"),
                                   fg=self.accent_color, 
                                   bg=self.bg_color)
        self.status_label.pack(pady=20)
        
        # Visual progress indicators
        self.step_frame = tk.Frame(install_frame, bg=self.bg_color)
        self.step_frame.pack(pady=20)
        
        # Run installation in thread
        install_thread = threading.Thread(target=self.run_installation)
        install_thread.start()
        
    def run_installation(self):
        """Run the actual installation process"""
        try:
            # Step 1: Python environment
            self.update_step_display("Setting up Python environment...", 4)
            self.log("Creating virtual environment...")
            
            if not os.path.exists("venv"):
                self.run_command(f"{sys.executable} -m venv venv")
                
            # Install Python dependencies
            pip_cmd = "venv\\Scripts\\pip.exe" if platform.system() == "Windows" else "venv/bin/pip"
            self.run_command(f"{pip_cmd} install -r omi_firmware/requirements.txt")
            self.run_command(f"{pip_cmd} install websockets pyserial requests")
            self.log("✓ Python environment ready", "success")
            
            # Step 2: Compile firmware
            self.update_step_display("Compiling firmware...", 5)
            
            firmware_paths = {
                1: "omi_firmware/esp32s3_ble/esp32s3_ble.ino",
                2: "omi_firmware/test_toggle_recording/test_toggle_recording.ino",
                3: "omi_firmware/test_oled_official/test_oled_official.ino"
            }
            
            firmware_path = firmware_paths[self.firmware_choice.get()]
            self.log(f"Compiling {firmware_path}...")
            
            success, _ = self.run_command(f"arduino-cli compile --fqbn esp32:esp32:XIAO_ESP32S3 {firmware_path}")
            if not success:
                raise Exception("Firmware compilation failed")
            self.log("✓ Firmware compiled successfully", "success")
            
            # Step 3: Upload firmware
            self.update_step_display("Uploading firmware to device...", 6)
            self.log(f"Uploading to {self.device_port}...")
            
            success, _ = self.run_command(f"arduino-cli upload --fqbn esp32:esp32:XIAO_ESP32S3 --port {self.device_port} {firmware_path}")
            if not success:
                self.log("Upload failed. Trying BOOT mode...", "warning")
                # Could add retry logic here
                raise Exception("Firmware upload failed")
            self.log("✓ Firmware uploaded successfully", "success")
            
            # Step 4: Start services (if full firmware)
            if self.firmware_choice.get() == 1:
                self.update_step_display("Starting services...", 7)
                self.start_services()
                
            # Step 5: Complete
            self.update_step_display("Installation complete!", 8)
            self.show_success_screen()
            
        except Exception as e:
            self.log(f"Installation failed: {str(e)}", "error")
            self.show_error_screen(str(e))
            
    def update_step_display(self, message, step):
        """Update the visual step display"""
        self.update_progress(step, message)
        self.status_label.config(text=message)
        
    def start_services(self):
        """Start companion services"""
        self.log("Starting Whisper transcription service...")
        if platform.system() == "Windows":
            subprocess.Popen(["start", "cmd", "/k", "cd omi_firmware && ..\\venv\\Scripts\\python esp32s3_companion.py"], shell=True)
        else:
            subprocess.Popen(["venv/bin/python", "omi_firmware/esp32s3_companion.py"])
            
        self.log("Starting bridge server...")
        if platform.system() == "Windows":
            subprocess.Popen(["start", "cmd", "/k", "venv\\Scripts\\python bridge_server.py"], shell=True)
        else:
            subprocess.Popen(["venv/bin/python", "bridge_server.py"])
            
        self.log("✓ Services started", "success")
        
    def show_success_screen(self):
        """Show installation success screen"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        success_frame = tk.Frame(self.content_frame, bg=self.bg_color)
        success_frame.pack(expand=True)
        
        # Success icon (big checkmark)
        icon = tk.Label(success_frame, 
                       text="✅", 
                       font=("Arial", 60),
                       bg=self.bg_color)
        icon.pack(pady=20)
        
        title = tk.Label(success_frame, 
                        text="Installation Complete!", 
                        font=("Arial", 24, "bold"),
                        fg=self.accent_color, 
                        bg=self.bg_color)
        title.pack()
        
        subtitle = tk.Label(success_frame, 
                          text="Your Brutally Honest AI device is ready to use",
                          font=("Arial", 14),
                          fg=self.fg_color, 
                          bg=self.bg_color)
        subtitle.pack(pady=10)
        
        # Instructions
        inst_frame = tk.Frame(success_frame, bg="#2a2a2a", relief=tk.RIDGE, bd=2)
        inst_frame.pack(pady=30, padx=50, fill=tk.BOTH)
        
        inst_title = tk.Label(inst_frame, 
                            text="📱 How to Use Your Device:", 
                            font=("Arial", 14, "bold"),
                            fg=self.accent_color, 
                            bg="#2a2a2a")
        inst_title.pack(anchor=tk.W, padx=20, pady=(15, 10))
        
        instructions = [
            "1. The OLED display shows 'Brutal Honest Query'",
            "2. Press the button once to START recording",
            "3. Press again to STOP recording",
            "4. LED blinks while recording",
            "5. Recordings are saved to SD card"
        ]
        
        for inst in instructions:
            label = tk.Label(inst_frame, 
                           text=inst, 
                           font=("Arial", 12),
                           fg=self.fg_color, 
                           bg="#2a2a2a")
            label.pack(anchor=tk.W, padx=40, pady=3)
            
        # Buttons
        button_frame = tk.Frame(success_frame, bg=self.bg_color)
        button_frame.pack(pady=20)
        
        if self.firmware_choice.get() == 1:
            web_btn = tk.Button(button_frame, 
                              text="🌐 Open Web Interface", 
                              command=lambda: webbrowser.open("http://localhost:3000"),
                              bg=self.accent_color, 
                              fg=self.bg_color,
                              font=("Arial", 12, "bold"),
                              padx=20, 
                              pady=10,
                              relief=tk.FLAT,
                              cursor="hand2")
            web_btn.pack(side=tk.LEFT, padx=5)
            
        monitor_btn = tk.Button(button_frame, 
                              text="📊 Open Serial Monitor", 
                              command=self.open_serial_monitor,
                              bg="#444444", 
                              fg=self.fg_color,
                              font=("Arial", 12),
                              padx=20, 
                              pady=10,
                              relief=tk.FLAT,
                              cursor="hand2")
        monitor_btn.pack(side=tk.LEFT, padx=5)
        
        close_btn = tk.Button(button_frame, 
                            text="Finish", 
                            command=self.quit_app,
                            bg="#666666", 
                            fg=self.fg_color,
                            font=("Arial", 12),
                            padx=30, 
                            pady=10,
                            relief=tk.FLAT,
                            cursor="hand2")
        close_btn.pack(side=tk.LEFT, padx=5)
        
    def show_error_screen(self, error_message):
        """Show installation error screen"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        error_frame = tk.Frame(self.content_frame, bg=self.bg_color)
        error_frame.pack(expand=True)
        
        # Error icon
        icon = tk.Label(error_frame, 
                       text="❌", 
                       font=("Arial", 60),
                       bg=self.bg_color)
        icon.pack(pady=20)
        
        title = tk.Label(error_frame, 
                        text="Installation Failed", 
                        font=("Arial", 24, "bold"),
                        fg=self.error_color, 
                        bg=self.bg_color)
        title.pack()
        
        error_label = tk.Label(error_frame, 
                             text=error_message,
                             font=("Arial", 12),
                             fg=self.fg_color, 
                             bg=self.bg_color,
                             wraplength=600)
        error_label.pack(pady=20)
        
        # Retry button
        retry_btn = tk.Button(error_frame, 
                            text="🔄 Retry Installation", 
                            command=self.restart_installation,
                            bg=self.accent_color, 
                            fg=self.bg_color,
                            font=("Arial", 12, "bold"),
                            padx=30, 
                            pady=10,
                            relief=tk.FLAT,
                            cursor="hand2")
        retry_btn.pack(pady=10)
        
    def open_serial_monitor(self):
        """Open Arduino serial monitor"""
        cmd = f"arduino-cli monitor --port {self.device_port}"
        if platform.system() == "Windows":
            subprocess.Popen(["start", "cmd", "/k", cmd], shell=True)
        else:
            subprocess.Popen(["gnome-terminal", "--", "bash", "-c", cmd])
            
    def restart_installation(self):
        """Restart the installation process"""
        self.current_step = 0
        self.install_button.config(state=tk.NORMAL)
        self.show_welcome_screen()
        self.progress_bar['value'] = 0
        self.progress_label.config(text="Ready to install")
        
    def start_installation(self):
        """Start the installation process"""
        self.log("Starting installation...", "success")
        
        # Check dependencies first
        if self.check_dependencies():
            self.show_device_selection()
        else:
            messagebox.showerror("Missing Dependencies", 
                               "Please install required dependencies and try again.")
            
    def quit_app(self):
        """Quit the application"""
        if messagebox.askokcancel("Quit", "Are you sure you want to quit?"):
            self.root.quit()
            
    def run(self):
        """Run the installer"""
        self.root.mainloop()

if __name__ == "__main__":
    installer = BrutallyHonestInstaller()
    installer.run()
