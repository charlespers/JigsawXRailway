# Railway Quick Fix Guide

## 🚀 What to Do RIGHT NOW

### 1. Set Environment Variables (5 minutes)

In Railway dashboard → Your Backend Service → **Variables** tab:

**Add these (replace with your actual keys):**
```
LLM_PROVIDER = xai
XAI_API_KEY = your_xai_key_here
```

**OR if using OpenAI:**
```
LLM_PROVIDER = openai  
OPENAI_API_KEY = your_openai_key_here
```

**Click "Add" for each, then Railway will auto-redeploy.**

### 2. Check Root Directory (2 minutes)

Railway Service → **Settings** → **Root Directory**:
- Should be **empty** (`.` or blank)
- This means Railway runs from repo root where `Procfile` is

### 3. Verify Procfile (1 minute)

Your `Procfile` should say:
```
web: cd charles_agentPCB_folder/api && python -m uvicorn server:app --host 0.0.0.0 --port $PORT
```

✅ This is correct - no changes needed.

### 4. Test After Deployment (2 minutes)

Wait for Railway to finish deploying, then test:

**In browser or curl:**
```
https://your-railway-url.railway.app/health
```

Should return: `{"status": "healthy", ...}`

**If health check works but analysis endpoints return 404:**

Check Railway logs for:
- Import errors in `routes/__init__.py`
- Errors loading `routes/analysis.py`
- Any Python syntax errors

### 5. Check Logs (2 minutes)

Railway Dashboard → **View Logs** → Look for:

✅ **Good signs:**
- `INFO:     Uvicorn running on http://0.0.0.0:PORT`
- `[PROVIDER] Set LLM_PROVIDER='xai'`
- No import errors

❌ **Bad signs:**
- `ModuleNotFoundError` - routes not found
- `404` errors in logs
- `API_KEY not found` - environment variable not set

## Common Issues & Quick Fixes

### Issue: "OpenAI_API_KEY not found" even with xAI
**Fix**: 
1. Check `LLM_PROVIDER` is set to `xai` (lowercase)
2. Check `XAI_API_KEY` is set (not `OPENAI_API_KEY`)
3. Redeploy after setting variables

### Issue: All endpoints return 404
**Fix**:
1. Check logs for import errors
2. Verify `routes/` directory is in deployment
3. Check Root Directory setting
4. Try redeploying

### Issue: Routes work locally but not on Railway
**Fix**:
1. Check Railway is using correct Root Directory
2. Verify all files are committed to git (Railway pulls from git)
3. Check build logs for errors

## That's It!

After setting environment variables and verifying Root Directory, Railway should work. The code fixes are already in place - you just need to configure Railway correctly.

**Total time: ~10 minutes**

