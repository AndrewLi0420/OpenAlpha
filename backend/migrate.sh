#!/bin/bash
# Migration helper script

set -e

echo "🔄 Running Database Migrations"
echo "=============================="
echo ""

cd "$(dirname "$0")"
source ../backend-venv/bin/activate

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "   Please create .env file with DATABASE_URI and other required variables"
    exit 1
fi

# Load .env variables
export $(cat .env | grep -v '^#' | xargs)

# Check if DATABASE_URI is set
if [ -z "$DATABASE_URI" ]; then
    echo "❌ DATABASE_URI not set in .env file"
    exit 1
fi

echo "📝 Generating migration..."
alembic revision --autogenerate -m "Initial schema"

echo ""
echo "✅ Migration generated!"
echo ""
echo "📝 Review the migration file in alembic/versions/"
echo ""
read -p "Apply migration now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔄 Applying migration..."
    alembic upgrade head
    echo ""
    echo "✅ Migration applied successfully!"
else
    echo "⏸️  Migration generated but not applied"
    echo "   Run 'alembic upgrade head' when ready"
fi

