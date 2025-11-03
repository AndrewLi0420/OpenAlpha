# Quick Start - Database Setup

## 🚀 Fast Track Setup

### 1. Install Docker Desktop
Download from: https://www.docker.com/products/docker-desktop

### 2. Start Services
```bash
cd /Users/andrewli/Desktop/personal\ projects/vibes
docker compose up -d postgres redis
```

### 3. Update .env
Make sure `backend/.env` has:
```
DATABASE_URI=postgresql://openalpha_user:openalpha_password@localhost:5432/openalpha
```

### 4. Run Migration
```bash
cd backend
source ../backend-venv/bin/activate
./migrate.sh
```

### 5. Test It
```bash
# Terminal 1: Start server
uvicorn app.main:app --reload

# Terminal 2: Test health
curl http://localhost:8000/api/v1/health
```

## ✅ Done!

Your database schema is now set up. See `NEXT_STEPS.md` for detailed instructions.

