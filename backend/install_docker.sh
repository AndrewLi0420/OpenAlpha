#!/bin/bash
# Install Docker Desktop via Homebrew

echo "🐳 Installing Docker Desktop..."
echo "==============================="
echo ""
echo "This will require your password for sudo"
echo ""

# Install via Homebrew
brew install --cask docker

echo ""
echo "✅ Docker Desktop installed!"
echo ""
echo "📝 Next steps:"
echo "1. Open Docker Desktop from Applications"
echo "2. Wait for Docker to start (whale icon in menu bar)"
echo "3. Run: cd /Users/andrewli/Desktop/personal\ projects/vibes && docker compose up -d postgres redis"
echo ""

