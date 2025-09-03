#!/bin/bash

# Create macOS DMG installer for Brutally Honest AI
# This script creates a beautiful DMG with custom background

set -e

echo "🎨 Creating Brutally Honest AI DMG installer..."

# Configuration
APP_NAME="Brutally Honest AI Installer"
DMG_NAME="BrutallyHonestAI-Installer"
DMG_FINAL="${DMG_NAME}.dmg"
VOLUME_NAME="Brutally Honest AI"
SOURCE_FOLDER="dmg_source"
DMG_TEMP="temp.dmg"

# Clean up any existing files
rm -rf "$SOURCE_FOLDER"
rm -f "$DMG_TEMP" "$DMG_FINAL"

# Create source folder structure
mkdir -p "$SOURCE_FOLDER"

# Create the app bundle
APP_BUNDLE="$SOURCE_FOLDER/${APP_NAME}.app"
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources"

# Create launcher script
cat > "$APP_BUNDLE/Contents/MacOS/launcher" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/../../../"
export PYTHONPATH="$PWD"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    osascript -e 'display alert "Python 3 Required" message "Please install Python 3 from python.org" buttons {"OK"} default button "OK"'
    open "https://www.python.org/downloads/"
    exit 1
fi

# Run the installer
python3 installer/installer_gui.py
EOF

chmod +x "$APP_BUNDLE/Contents/MacOS/launcher"

# Create Info.plist
cat > "$APP_BUNDLE/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Brutally Honest AI Installer</string>
    <key>CFBundleDisplayName</key>
    <string>Brutally Honest AI Installer</string>
    <key>CFBundleIdentifier</key>
    <string>com.brutallyhonest.installer</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSMinimumSystemVersion</key>
    <string>10.12</string>
</dict>
</plist>
EOF

# Copy all necessary files
cp -r ../omi_firmware "$SOURCE_FOLDER/"
cp -r ../frontend "$SOURCE_FOLDER/"
cp -r ../installer "$SOURCE_FOLDER/"
cp ../bridge_server.py "$SOURCE_FOLDER/"
cp ../install_brutally_honest.sh "$SOURCE_FOLDER/"
cp ../INSTALLER_README.md "$SOURCE_FOLDER/README.md"

# Create a simple icon (you can replace with actual icon)
cat > "$APP_BUNDLE/Contents/Resources/AppIcon.icns" << 'EOF'
# Placeholder for icon - in production, use iconutil to create proper .icns
EOF

# Create DMG background image using ImageMagick (if available)
if command -v magick &> /dev/null; then
    echo "Creating custom DMG background..."
    magick -size 600x400 xc:'#1a1a1a' \
            -font Arial -pointsize 36 -fill '#00ff88' \
            -annotate +300+80 'Brutally Honest AI' \
            -font Arial -pointsize 18 -fill white \
            -annotate +300+120 'Drag to Applications folder to install' \
            "$SOURCE_FOLDER/.background.png"
elif command -v convert &> /dev/null; then
    echo "Creating custom DMG background..."
    convert -size 600x400 xc:'#1a1a1a' \
            -font Arial -pointsize 36 -fill '#00ff88' \
            -annotate +300+80 'Brutally Honest AI' \
            -font Arial -pointsize 18 -fill white \
            -annotate +300+120 'Drag to Applications folder to install' \
            "$SOURCE_FOLDER/.background.png"
else
    echo "ImageMagick not found, skipping custom background"
fi

# Create Applications symlink
ln -s /Applications "$SOURCE_FOLDER/Applications"

# Create the initial DMG
echo "Creating DMG..."
hdiutil create -srcfolder "$SOURCE_FOLDER" -volname "$VOLUME_NAME" -fs HFS+ \
               -fsargs "-c c=64,a=16,e=16" -format UDRW "$DMG_TEMP"

# Mount the DMG
echo "Mounting DMG..."
DEVICE=$(hdiutil attach -readwrite -noverify -noautoopen "$DMG_TEMP" | \
         egrep '^/dev/' | sed 1q | awk '{print $1}')

# Wait for mount
sleep 2

# Set view options
echo "Setting DMG window properties..."
osascript << EOF
tell application "Finder"
    tell disk "$VOLUME_NAME"
        open
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set bounds of container window to {100, 100, 700, 500}
        set position of container window to {100, 100}
        set viewOptions to the icon view options of container window
        set arrangement of viewOptions to not arranged
        set icon size of viewOptions to 128
        
        -- Try to set background if it exists
        try
            set background picture of viewOptions to file ".background.png"
        end try
        
        -- Position items
        try
            set position of item "$APP_NAME" of container window to {150, 200}
            set position of item "Applications" of container window to {450, 200}
        end try
        
        close
        open
        update without registering applications
        delay 2
    end tell
end tell
EOF

# Create custom volume icon (optional)
# cp "VolumeIcon.icns" "/Volumes/$VOLUME_NAME/.VolumeIcon.icns"
# SetFile -a C "/Volumes/$VOLUME_NAME"

# Unmount
echo "Unmounting DMG..."
hdiutil detach "$DEVICE"

# Convert to compressed DMG
echo "Compressing DMG..."
hdiutil convert "$DMG_TEMP" -format UDZO -imagekey zlib-level=9 -o "$DMG_FINAL"

# Clean up
rm -f "$DMG_TEMP"
rm -rf "$SOURCE_FOLDER"

# Sign the DMG (if you have a certificate)
# codesign --sign "Developer ID Application: Your Name" "$DMG_FINAL"

echo "✅ DMG created successfully: $DMG_FINAL"
echo "📦 File size: $(du -h "$DMG_FINAL" | cut -f1)"

# Open in Finder
open -R "$DMG_FINAL"
