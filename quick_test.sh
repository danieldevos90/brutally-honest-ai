#!/bin/bash

# Quick Test Script for Voice Insight Platform
# Tests the system step by step

set -e

echo "🚀 Voice Insight Platform - Quick Test"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Test 1: Check if we're in the right directory
echo ""
echo "📁 Checking project structure..."
if [ -f "main.py" ] && [ -f "requirements.txt" ] && [ -d "src" ]; then
    print_status 0 "Project structure looks good"
else
    print_status 1 "Not in project root directory or missing files"
    exit 1
fi

# Test 2: Check Python
echo ""
echo "🐍 Checking Python environment..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_status 0 "Python available: $PYTHON_VERSION"
else
    print_status 1 "Python3 not found"
    exit 1
fi

# Test 3: Check virtual environment
echo ""
echo "📦 Checking virtual environment..."
if [ -d "venv" ]; then
    print_status 0 "Virtual environment exists"
    
    # Activate and test
    source venv/bin/activate
    if [ "$VIRTUAL_ENV" != "" ]; then
        print_status 0 "Virtual environment activated"
    else
        print_status 1 "Failed to activate virtual environment"
    fi
else
    print_warning "Virtual environment not found. Creating..."
    python3 -m venv venv
    source venv/bin/activate
    pip install pyserial numpy
    print_status 0 "Virtual environment created and activated"
fi

# Test 4: Check Docker
echo ""
echo "🐳 Checking Docker..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    print_status 0 "Docker available: $DOCKER_VERSION"
    
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version)
        print_status 0 "Docker Compose available: $COMPOSE_VERSION"
    else
        print_status 1 "Docker Compose not found"
    fi
else
    print_status 1 "Docker not found"
fi

# Test 5: Check configuration
echo ""
echo "⚙️ Checking configuration..."
if [ -f ".env" ]; then
    print_status 0 ".env file exists"
else
    if [ -f "env.example" ]; then
        cp env.example .env
        print_status 0 ".env file created from template"
        print_warning "Please edit .env file with your configuration"
    else
        print_status 1 "No .env or env.example file found"
    fi
fi

# Test 6: Test basic imports
echo ""
echo "🧪 Testing basic imports..."
python3 test_basic.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    print_status 0 "Basic component tests passed"
else
    print_warning "Some basic tests failed. Run 'python test_basic.py' for details"
fi

# Test 7: Check for OMI hardware
echo ""
echo "🎙️ Checking for OMI DevKit 2..."
python3 setup.py --check-omi 2>/dev/null | grep -q "omi\|pico" 
if [ $? -eq 0 ]; then
    print_status 0 "OMI DevKit 2 detected!"
else
    print_warning "OMI DevKit 2 not detected. Connect via USB-C to test hardware."
fi

# Test 8: Docker Compose validation
echo ""
echo "🔧 Validating Docker Compose..."
docker-compose config > /dev/null 2>&1
if [ $? -eq 0 ]; then
    print_status 0 "Docker Compose configuration valid"
else
    print_status 1 "Docker Compose configuration has errors"
fi

# Summary
echo ""
echo "📊 Quick Test Summary"
echo "===================="
echo ""
echo "✅ Ready to proceed with:"
echo "   1. Connect OMI DevKit 2 via USB-C (if not already)"
echo "   2. Edit .env file with your configuration"
echo "   3. Start services: ./scripts/start_services.sh"
echo "   4. Install full dependencies: pip install -r requirements.txt"
echo "   5. Run the platform: python main.py"
echo ""
echo "📖 For detailed testing, see:"
echo "   - TESTING.md - Comprehensive testing guide"
echo "   - TEST_RESULTS.md - Current test status"
echo ""
echo "🎯 Test individual components:"
echo "   - python scripts/test_omi.py --test-connection"
echo "   - curl http://localhost:8000/api/status (after starting)"
echo ""

deactivate 2>/dev/null || true
echo "🎉 Quick test completed!"
