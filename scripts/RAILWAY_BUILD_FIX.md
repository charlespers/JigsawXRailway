# Railway Build Fix

## Issue
Railway is showing "waiting for the build to start" - this means Railway isn't detecting the build properly.

## Solution

### Option 1: Set Root Directory in Railway Dashboard
1. Go to your Railway project settings
2. Under "Settings" → "Service" → "Root Directory"
3. Set it to: `backend`
4. Save and redeploy

### Option 2: Use Railway CLI
```bash
railway link
railway variables set RAILWAY_ROOT_DIR=backend
railway up
```

### Option 3: Move nixpacks.toml to Root
If Railway still doesn't detect, you may need to:
1. Copy `backend/nixpacks.toml` to the root directory
2. Update the paths in it to be relative to root
3. Update `railway.json` to point to the correct directory

## Current Configuration

- **Procfile**: Points to `backend/api`
- **nixpacks.toml**: Located in `backend/`
- **railway.json**: At root, should work with root directory set

## Quick Fix
The easiest solution is to set the **Root Directory** in Railway dashboard to `backend`.

