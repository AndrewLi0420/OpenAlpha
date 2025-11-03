# Install Docker Desktop - Step by Step

## Option 1: Download and Install (Recommended for macOS)

1. **Download Docker Desktop:**
   - Go to: https://www.docker.com/products/docker-desktop
   - Click "Download for Mac"
   - Choose version for your Mac (Intel or Apple Silicon)

2. **Install:**
   - Open the downloaded `.dmg` file
   - Drag Docker.app to Applications folder
   - Open Docker from Applications
   - Follow the setup wizard
   - Enter your password when prompted

3. **Wait for Docker to start:**
   - Look for Docker whale icon in menu bar (top right)
   - Wait until it says "Docker Desktop is running"
   - This may take 1-2 minutes on first start

4. **Verify installation:**
   ```bash
   docker --version
   docker compose version
   ```

## Option 2: Install via Homebrew (If you have Homebrew)

```bash
brew install --cask docker
open -a Docker
```

## After Installation

Once Docker is running, come back here and we'll:
1. Start PostgreSQL and Redis
2. Generate the database migration
3. Apply the migration
4. Test everything

## Quick Test

After Docker starts, run:
```bash
cd /Users/andrewli/Desktop/personal\ projects/vibes
docker compose up -d postgres redis
docker compose ps
```

You should see postgres and redis services running!

