# Next Steps - Complete Database Setup

## ✅ What's Been Completed

1. ✅ All SQLAlchemy models created
2. ✅ Foreign keys and relationships defined
3. ✅ Indexes added
4. ✅ Pydantic schemas created
5. ✅ Test structure created
6. ✅ Migration and setup scripts created

## 📋 Step-by-Step Setup

### Step 1: Install Database Services

**Option A: Docker (Recommended)**
```bash
# Install Docker Desktop from: https://www.docker.com/products/docker-desktop
# Then run:
cd /Users/andrewli/Desktop/personal\ projects/vibes
./backend/setup_db.sh
```

**Option B: Local Installation (macOS)**
```bash
brew install postgresql@15 redis
brew services start postgresql@15
brew services start redis
createdb openalpha
```

### Step 2: Update .env File

Make sure your `backend/.env` file has the correct DATABASE_URI:

**For Docker setup:**
```
DATABASE_URI=postgresql://openalpha_user:openalpha_password@localhost:5432/openalpha
```

**For local PostgreSQL:**
```
DATABASE_URI=postgresql://$(whoami)@localhost:5432/openalpha
```

### Step 3: Generate and Run Migration

```bash
cd backend
source ../backend-venv/bin/activate
./migrate.sh
```

Or manually:
```bash
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

### Step 4: Test the Setup

**Test database connection:**
```bash
# Start the server
uvicorn app.main:app --reload

# In another terminal, test health endpoint
curl http://localhost:8000/api/v1/health
```

**Run unit tests:**
```bash
# Install test dependencies if needed
pip install pytest-asyncio aiosqlite

# Run tests
pytest tests/
```

### Step 5: Verify Everything Works

1. ✅ Check `/api/v1/health` returns `database_is_online: true`
2. ✅ Check that superuser was created on startup
3. ✅ Run `pytest tests/test_models/` to verify models work
4. ✅ Run `pytest tests/test_migrations/` to verify schema

## 🔧 Troubleshooting

**Migration fails?**
- Check database is running: `docker compose ps` or `brew services list`
- Verify DATABASE_URI in .env matches your setup
- Check database exists: `psql -l` (Docker) or `createdb openalpha` (local)

**Tests fail?**
- Install dependencies: `pip install pytest-asyncio aiosqlite`
- Check that models are imported correctly

**Health endpoint shows database offline?**
- Verify PostgreSQL is running
- Check DATABASE_URI format is correct
- Try connecting manually: `psql $DATABASE_URI`

## 📝 After Setup

Once everything is working:

1. Mark migration tasks as complete in the story file
2. Run full test suite
3. Update story status to "review"
4. Commit your changes

