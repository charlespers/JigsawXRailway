# Railway Setup Guide

## Required Configuration

### 1. Environment Variables (CRITICAL)

Go to your Railway project → Backend service → **Variables** tab and add:

#### ✅ REQUIRED:

```
XAI_API_KEY=your-xai-api-key-here
```

**Without this, LLM features won't work!**

#### ⚙️ RECOMMENDED (for production):

```
CORS_ORIGINS=https://jigsawxrailway-frontend.up.railway.app
```

**This allows your frontend to connect. If not set, defaults to `*` (allows all).**

#### ⚙️ OPTIONAL:

```
LOG_LEVEL=INFO
```

**Default is INFO. Set to DEBUG for more verbose logs.**

#### ❌ DO NOT SET:

```
PORT
```

**Railway automatically sets this - don't set it manually!**

---

## Railway Service Configuration

### Build Settings

- ✅ **Builder**: Nixpacks (configured in `railway.json`)
- ✅ **Start Command**: Automatically detected from `nixpacks.toml`
- ✅ **Python Version**: 3.11 (specified in `nixpacks.toml`)

### Health Checks (Optional but Recommended)

Railway can automatically check if your service is healthy:

1. Go to your service → **Settings** → **Health Check**
2. Set:
   - **Path**: `/health`
   - **Timeout**: 30 seconds
   - **Interval**: 30 seconds

This will help Railway detect if your backend crashes and restart it.

---

## Deployment Checklist

### Before First Deploy:

- [ ] Set `XAI_API_KEY` environment variable
- [ ] (Optional) Set `CORS_ORIGINS` to your frontend URL
- [ ] (Optional) Configure health check

### After Deploy:

- [ ] Check logs to ensure server started
- [ ] Test `/health` endpoint: `https://your-backend.up.railway.app/health`
- [ ] Test `/docs` endpoint: `https://your-backend.up.railway.app/docs`
- [ ] Verify CORS is working (check browser console)

---

## Common Issues

### Backend Not Starting

- Check Railway logs for errors
- Verify `XAI_API_KEY` is set (app will start but LLM features won't work)
- Check that `requirements.txt` has all dependencies

### CORS Errors

- Set `CORS_ORIGINS` to your frontend URL: `https://jigsawxrailway-frontend.up.railway.app`
- Or leave unset to allow all origins (`*`)

### Parts Database Not Found

- This is a warning, not an error
- App will still work, just without parts data
- Check logs to see which paths were tried

---

## Quick Setup Steps

1. **Go to Railway Dashboard**

   - Select your backend service
   - Click **Variables** tab

2. **Add Required Variable**:

   ```
   Name: XAI_API_KEY
   Value: [your xAI API key]
   ```

3. **Add CORS (Recommended)**:

   ```
   Name: CORS_ORIGINS
   Value: https://jigsawxrailway-frontend.up.railway.app
   ```

4. **Save** - Railway will automatically redeploy

5. **Wait for deployment** - Check logs to confirm it started

6. **Test**:
   - Health: `https://outstanding-warmth-backend.up.railway.app/health`
   - Docs: `https://outstanding-warmth-backend.up.railway.app/docs`

---

## That's It!

The backend is configured via:

- ✅ `railway.json` - Build configuration
- ✅ `nixpacks.toml` - Build steps and start command
- ✅ Environment variables - Runtime configuration

No other Railway-specific setup needed!
