# 502 Error Debugging Guide

## Problem
Railway edge proxy returns 502: "Application failed to respond" for OPTIONS requests.

## What This Means
The app isn't responding to requests. Possible causes:

1. **App not starting** - Check Railway logs for startup errors
2. **App crashing on startup** - Import errors, missing dependencies, etc.
3. **Wrong port** - App not listening on PORT env var
4. **Railway timeout** - App taking too long to start

## What I've Fixed

1. **Ultra-simple OPTIONS handler** - No dependencies, no settings access, just returns CORS headers
2. **Middleware runs FIRST** - Intercepts OPTIONS before any route handlers
3. **Startup logging** - Added startup event to verify app starts

## How to Debug

### Check Railway Logs
Look for:
- `INFO: Uvicorn running on http://0.0.0.0:8080` - App started successfully
- `🚀 Application starting up...` - Startup event fired
- Any import errors or exceptions

### Test Locally
```bash
cd backend
python3 -m app.main
# Should see: INFO: Uvicorn running on http://0.0.0.0:8000
```

### Test OPTIONS with curl
```bash
curl -X OPTIONS http://localhost:8000/mcp/component-analysis \
  -H "Origin: https://jigsawxrailway-frontend.up.railway.app" \
  -v
# Should return 200 with CORS headers
```

## If Still Getting 502

1. **Check Railway logs** - Is the app starting?
2. **Check PORT env var** - Railway sets PORT, app should use it
3. **Check startup command** - `/opt/venv/bin/python -m app.main` in railway.json
4. **Check dependencies** - Are all packages installed?

## Current Status

- ✅ OPTIONS handler is ultra-simple (no dependencies)
- ✅ Middleware runs first
- ✅ Startup logging added
- ⚠️ Need to verify app actually starts on Railway

