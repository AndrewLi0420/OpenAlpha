# Database Setup Guide

## Option 1: Using Docker (Recommended)

### Step 1: Install Docker Desktop

**macOS:**
1. Download Docker Desktop from: https://www.docker.com/products/docker-desktop
2. Install and start Docker Desktop
3. Wait for Docker to start (check the menu bar icon)

**Then run:**
```bash
cd /Users/andrewli/Desktop/personal\ projects/vibes
docker compose up -d postgres redis
```

This will start PostgreSQL and Redis in containers.

### Step 2: Verify Services are Running

```bash
docker compose ps
```

You should see `postgres` and `redis` services with status "Up".

### Step 3: Continue with Migration

Once Docker services are running, proceed to generate migrations.

## Option 2: Local PostgreSQL Installation

### macOS (using Homebrew):

```bash
brew install postgresql@15
brew services start postgresql@15
createdb openalpha
```

Update `.env` file:
```
DATABASE_URI=postgresql://$(whoami)@localhost:5432/openalpha
```

### Then Install Redis:

```bash
brew install redis
brew services start redis
```

## Next Steps

Once database is running:

1. Generate migration: `alembic revision --autogenerate -m "Initial schema"`
2. Apply migration: `alembic upgrade head`
3. Test connection: Start the FastAPI server and check `/api/v1/health`

