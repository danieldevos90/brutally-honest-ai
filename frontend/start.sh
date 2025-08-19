#!/bin/bash

echo "🎙️ Starting Voice Insight Frontend..."
echo "====================================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

echo "🚀 Starting frontend server..."
echo "Frontend will be available at: http://localhost:3000"
echo "WebSocket proxy will be available at: ws://localhost:3001"
echo ""
echo "Make sure your Voice Insight Platform backend is running at http://localhost:8000"
echo ""

# Start the server
npm start
