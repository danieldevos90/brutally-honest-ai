#!/bin/bash

# Voice Insight Platform - Service Startup Script

set -e

echo "🚀 Starting Voice Insight Platform Services..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start databases
echo "📊 Starting databases..."
docker-compose up -d postgres qdrant

# Wait for databases to be ready
echo "⏳ Waiting for databases to be ready..."
sleep 10

# Start Ollama
echo "🧠 Starting Ollama LLM service..."
docker-compose up -d ollama

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
sleep 15

# Pull the LLM model if not already present
echo "📥 Checking/pulling LLM model..."
docker exec brutally-honest-ai-ollama-1 ollama pull mistral:7b || echo "Model already exists or pull failed"

# Check service health
echo "🔍 Checking service health..."

# Check PostgreSQL
if docker-compose exec postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready"
fi

# Check Qdrant
if curl -f http://localhost:6333/health > /dev/null 2>&1; then
    echo "✅ Qdrant is ready"
else
    echo "❌ Qdrant is not ready"
fi

# Check Ollama
if curl -f http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is ready"
else
    echo "❌ Ollama is not ready"
fi

echo ""
echo "🎉 Services started! You can now run:"
echo "   python main.py"
echo ""
echo "📊 Service URLs:"
echo "   - Voice Insight API: http://localhost:8000"
echo "   - PostgreSQL: localhost:5432"
echo "   - Qdrant: http://localhost:6333"
echo "   - Ollama: http://localhost:11434"
echo ""
echo "🔧 To stop services: docker-compose down"
