#!/bin/bash
# Database setup helper script

set -e

echo "🔧 Database Setup Helper"
echo "======================"
echo ""

# Check for Docker
if command -v docker &> /dev/null; then
    echo "✅ Docker found"
    
    # Check if Docker is running
    if docker info &> /dev/null; then
        echo "✅ Docker is running"
        echo ""
        echo "Starting PostgreSQL and Redis containers..."
        cd "$(dirname "$0")/.."
        docker compose up -d postgres redis
        
        echo ""
        echo "⏳ Waiting for PostgreSQL to be ready..."
        sleep 5
        
        echo ""
        echo "✅ Services started!"
        echo ""
        echo "Database connection:"
        echo "  Host: localhost"
        echo "  Port: 5432"
        echo "  Database: openalpha"
        echo "  User: openalpha_user"
        echo "  Password: openalpha_password"
        echo ""
        echo "📝 Make sure your .env file has:"
        echo "   DATABASE_URI=postgresql://openalpha_user:openalpha_password@localhost:5432/openalpha"
        echo ""
    else
        echo "❌ Docker is installed but not running"
        echo "   Please start Docker Desktop and try again"
        exit 1
    fi
else
    echo "❌ Docker not found"
    echo ""
    echo "Please install Docker Desktop:"
    echo "  macOS: https://www.docker.com/products/docker-desktop"
    echo ""
    echo "Or install PostgreSQL locally:"
    echo "  brew install postgresql@15 redis"
    echo "  brew services start postgresql@15"
    echo "  brew services start redis"
    echo "  createdb openalpha"
    exit 1
fi

