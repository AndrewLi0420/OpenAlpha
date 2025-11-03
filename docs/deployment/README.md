# Deployment Guide - OpenAlpha

This guide covers free-tier deployment configuration for OpenAlpha using Vercel (frontend), Render (backend), and Supabase (optional PostgreSQL alternative).

## Table of Contents

1. [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
2. [Backend Deployment (Render)](#backend-deployment-render)
3. [Database Options](#database-options)
4. [Free-Tier Limits and Constraints](#free-tier-limits-and-constraints)

## Frontend Deployment (Vercel)

### Prerequisites

- Vercel account (free tier available)
- GitHub/GitLab/Bitbucket repository connected to Vercel

### Deployment Steps

1. **Import Project**
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Click "Add New Project"
   - Import your repository

2. **Configure Build Settings**
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend` (if monorepo) or leave blank if frontend is root
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
   - **Install Command:** `npm install`

3. **Environment Variables**
   - Add the following environment variable:
     - `VITE_API_URL` = `https://openalpha-backend.onrender.com` (or your Render backend URL)

4. **Deploy**
   - Click "Deploy"
   - Vercel will automatically build and deploy your frontend
   - Your site will be available at `https://your-project.vercel.app`

### Vercel Free-Tier Limits

- **Builds:** 6000 build minutes/month
- **Bandwidth:** 100GB/month
- **Serverless Functions:** 100GB-hours execution time
- **Custom Domains:** Unlimited (free)
- **HTTPS:** Included (automatic SSL)

## Backend Deployment (Render)

### Prerequisites

- Render account (free tier available)
- GitHub repository
- PostgreSQL service (Render provides free tier)

### Deployment Steps

1. **Create PostgreSQL Database**
   - Go to Render Dashboard → "New" → "PostgreSQL"
   - Name: `openalpha-db`
   - Database: `openalpha`
   - User: Auto-generated (note credentials)
   - Plan: Free
   - Click "Create Database"
   - Wait for database to be ready
   - Copy the "Internal Database URL" (for Render services) or "External Database URL" (for local/other services)

2. **Create Web Service (Backend)**
   - Go to Render Dashboard → "New" → "Web Service"
   - Connect your GitHub repository
   - **Name:** `openalpha-backend`
   - **Region:** Choose closest to your users
   - **Branch:** `main` or your deployment branch
   - **Root Directory:** `backend` (if monorepo)
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. **Configure Environment Variables**
   Add the following environment variables in Render dashboard:
   
   ```
   ENVIRONMENT=prod
   DEBUG=false
   SECRET_KEY=<generate-a-secure-random-string>
   DATABASE_URL=<from-postgres-service-internal-url>
   REDIS_URL=redis://<redis-service-url>:6379 (if using Redis)
   SERVER_HOST=https://openalpha-backend.onrender.com
   BACKEND_CORS_ORIGINS=https://your-project.vercel.app
   DEFAULT_FROM_EMAIL=noreply@openalpha.com
   DEFAULT_FROM_NAME=OpenAlpha
   RESEND_API_KEY=<your-resend-api-key>
   FIRST_SUPERUSER_EMAIL=admin@openalpha.com
   FIRST_SUPERUSER_PASSWORD=<secure-password>
   SENTRY_DSN=<optional-sentry-dsn>
   ```

4. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy your backend
   - Your API will be available at `https://openalpha-backend.onrender.com`

### Render Free-Tier Limits

**Web Services:**
- **CPU:** 0.1 CPU shared
- **RAM:** 512MB
- **Bandwidth:** 100GB/month
- **Sleep after 15 minutes of inactivity** (wakes on first request, ~30s wake time)
- **Custom Domains:** Supported

**PostgreSQL:**
- **Database Size:** 1GB storage
- **Connections:** 95 max connections
- **Backups:** Manual (7-day retention on paid plans)
- **Note:** Database persists even when web service sleeps

## Database Options

### Option 1: Render PostgreSQL (Recommended for Free Tier)

- **Pros:** Easy setup, integrated with Render services, persistent storage
- **Cons:** 1GB limit, sleeps with web service (but database persists)
- **Best for:** Development, small projects, learning

### Option 2: Supabase PostgreSQL (Alternative)

- **Pros:** 500MB free tier, PostgreSQL 15+, built-in REST API, real-time subscriptions
- **Cons:** Separate service, need to configure connection separately
- **Setup:**
  1. Create account at [Supabase](https://supabase.com)
  2. Create new project
  3. Get connection string from Project Settings → Database
  4. Update `DATABASE_URL` in Render environment variables
  5. Use connection string format: `postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres`

**Supabase Free-Tier Limits:**
- **Database Size:** 500MB
- **API Requests:** 50,000/month
- **Auth Users:** 50,000
- **File Storage:** 1GB

## Free-Tier Limits and Constraints

### General Considerations

1. **Cold Starts:** Render free tier services sleep after 15 minutes. First request may take ~30 seconds.
2. **Resource Limits:** CPU and RAM are shared, may affect performance under load.
3. **Storage Limits:** 
   - Render PostgreSQL: 1GB
   - Supabase: 500MB
4. **Bandwidth:** 100GB/month (usually sufficient for small projects)
5. **Backup Strategy:** Manual backups recommended (Render free tier doesn't include automatic backups)

### Recommended Upgrades (When Needed)

**Render Paid Plans:**
- **Starter ($7/month):** No sleep, 512MB RAM, better performance
- **Standard ($25/month):** 2GB RAM, dedicated resources

**Vercel Paid Plans:**
- **Pro ($20/month):** More build minutes, team features, analytics

### Monitoring and Scaling

1. **Monitor Usage:** Check Render and Vercel dashboards regularly
2. **Database Growth:** Monitor PostgreSQL size; upgrade before hitting limits
3. **Performance:** Use Render metrics to track response times
4. **Error Tracking:** Consider Sentry (free tier available) for production monitoring

## Troubleshooting

### Backend Won't Start
- Check environment variables are set correctly
- Verify `DATABASE_URL` format (use internal URL for Render services)
- Check logs in Render dashboard

### Database Connection Issues
- Verify `DATABASE_URL` uses internal connection string within Render network
- Check database service is running in Render dashboard
- Ensure firewall rules allow connections

### CORS Errors
- Verify `BACKEND_CORS_ORIGINS` includes your Vercel frontend URL
- Check environment variable formatting (comma-separated, no spaces unless in quotes)

### Build Failures
- Check build logs in Vercel/Render dashboards
- Verify all dependencies are in `package.json` / `requirements.txt`
- Ensure Node.js/Python versions are compatible

## Next Steps

After deployment:
1. Update frontend `.env.production` with actual backend URL
2. Test all API endpoints
3. Verify database migrations have run (`alembic upgrade head`)
4. Create initial superuser via backend admin or initial data script
5. Set up monitoring (Sentry, logging)
6. Configure custom domains if desired

