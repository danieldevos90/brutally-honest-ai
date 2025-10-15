#!/bin/bash

# BrutallyHonest.io Landing Page - Vercel Deployment Script

echo "🚀 BrutallyHonest.io Deployment Script"
echo "========================================"
echo ""

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "📦 Vercel CLI not found. Installing..."
    npm install -g vercel
    echo ""
fi

echo "✓ Vercel CLI installed"
echo ""

# Ask for deployment type
echo "Select deployment type:"
echo "1) Preview deployment (test before going live)"
echo "2) Production deployment (live site)"
echo ""
read -p "Enter choice (1 or 2): " choice

echo ""

if [ "$choice" = "1" ]; then
    echo "🧪 Deploying to preview..."
    vercel
elif [ "$choice" = "2" ]; then
    echo "🌐 Deploying to production..."
    echo "⚠️  This will update your live site!"
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        vercel --prod
    else
        echo "❌ Deployment cancelled"
        exit 1
    fi
else
    echo "❌ Invalid choice"
    exit 1
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🎉 Your landing page is live!"

