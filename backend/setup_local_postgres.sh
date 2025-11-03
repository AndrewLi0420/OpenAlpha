#!/bin/bash
# Setup PostgreSQL and Redis locally (no Docker needed)

set -e

echo "🗄️  Setting up PostgreSQL and Redis locally"
echo "============================================"
echo ""

# Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew not found. Please install it first:"
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

echo "📦 Installing PostgreSQL 15..."
brew install postgresql@15

echo ""
echo "📦 Installing Redis..."
brew install redis

echo ""
echo "🚀 Starting services..."
brew services start postgresql@15
brew services start redis

echo ""
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 3

echo ""
echo "🗄️  Creating database..."
createdb openalpha || echo "Database might already exist (that's okay)"

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Update your .env file with:"
echo "   DATABASE_URI=postgresql://$(whoami)@localhost:5432/openalpha"
echo ""
echo "📝 Or keep Docker config:"
echo "   DATABASE_URI=postgresql://openalpha_user:openalpha_password@localhost:5432/openalpha"
echo "   (if you create user manually: createuser -P openalpha_user)"
echo ""

