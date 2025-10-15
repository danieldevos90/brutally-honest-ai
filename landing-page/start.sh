#!/bin/bash

# BrutallyHonest.io Landing Page Startup Script

echo "🚀 Starting BrutallyHonest.io Landing Page..."
echo ""

# Check if node is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    echo "Visit: https://nodejs.org/"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

echo "✓ Node.js $(node --version) detected"
echo "✓ npm $(npm --version) detected"
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo ""
fi

# Check if .env file exists, if not create from example
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        echo "⚙️  Creating .env file from env.example..."
        cp env.example .env
        echo "✓ .env file created. Please update with your values if needed."
        echo ""
    fi
fi

# Start the server
echo "🌐 Starting server..."
echo "📍 Local: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

npm start

