# Railway Setup - Step by Step

## ✅ What You Need to Do on Railway

### Step 1: Set Environment Variables

1. Go to your Railway project dashboard
2. Click on your **backend service** (the one running the Python/FastAPI app)
3. Go to the **Variables** tab
4. Add these environment variables:

#### If using xAI:
```
LLM_PROVIDER = xai
XAI_API_KEY = your_actual_xai_api_key_here
```

#### If using OpenAI:
```
LLM_PROVIDER = openai
OPENAI_API_KEY = your_actual_openai_api_key_here
```

#### Optional (but recommended):
```
XAI_MODEL = grok-3
XAI_TEMPERATURE = 0.3
```

**Important**: 
- Variable names are **case-sensitive** - use exact names shown above
- No quotes needed around values
- Click **Add** after each variable
- Click **Deploy** or wait for auto-deploy after adding variables

### Step 2: Verify Your Procfile

Your `Procfile` should contain:
```
web: cd backend/api && python -m uvicorn server:app --host 0.0.0.0 --port $PORT
```

✅ This looks correct in your setup.

### Step 3: Check Root Directory

Railway needs to know where your project root is. Make sure:
- Your `Procfile` is in the **root** of your repository (where Railway is looking)
- Your `railway.json` is in the root
- The path `backend/api/server.py` exists from the root

### Step 4: Verify Deployment

After Railway deploys (or trigger a new deployment):

1. **Check Health Endpoint**:
   ```
   https://your-railway-url.railway.app/health
   ```
   Should return: `{"status": "healthy", ...}`

2. **Check Routes**:
   ```
   https://your-railway-url.railway.app/api/v1/routes
   ```
   Should list all routes including `/api/v1/analysis/*`

3. **Test Analysis Endpoint**:
   ```
   POST https://your-railway-url.railway.app/api/v1/analysis/validation
   ```
   Should return 200 (not 404)

### Step 5: Check Logs

In Railway dashboard:
1. Go to your service
2. Click **View Logs**
3. Look for:
   - ✅ `[PROVIDER] Set LLM_PROVIDER='xai'` messages
   - ✅ Route registration messages
   - ❌ Any 404 errors
   - ❌ Any import errors
   - ❌ Any "API_KEY not found" errors

### Step 6: If Routes Still Return 404

**Possible Issues:**

1. **Routes not being registered**:
   - Check logs for import errors in `routes/__init__.py`
   - Verify `routes/analysis.py` exists and is valid
   - Check that `app.include_router(api_router)` is executing

2. **Wrong working directory**:
   - Your Procfile uses `cd backend/api`
   - Make sure Railway is running from the repo root
   - Check Railway service settings → **Root Directory** (should be repo root)

3. **Port issues**:
   - Railway automatically sets `PORT` environment variable
   - Your code uses `os.environ.get("PORT", 3001)` - this should work
   - Check that Railway service is set to use the `web` process from Procfile

### Step 7: Force Redeploy

After setting environment variables:
1. Go to **Deployments** tab
2. Click **Redeploy** on the latest deployment
3. Wait for build to complete
4. Test endpoints again

## ⚠️ IMPORTANT: Check Your Railway Service Root Directory

Railway needs to know where to run from. Check your Railway service settings:

1. Go to your Railway service → **Settings**
2. Check **Root Directory**:
   - If Railway is connected to the **repo root** (where `Procfile` is): Root Directory should be **empty** or **`.`**
   - If Railway is connected to `backend`: Root Directory should be **`backend`**

**Most likely**: Railway is connected to repo root, so Root Directory should be empty.

## Quick Checklist

- [ ] Environment variables set (`LLM_PROVIDER`, `XAI_API_KEY` or `OPENAI_API_KEY`)
- [ ] Variables saved (not just typed)
- [ ] Service redeployed after setting variables
- [ ] `/health` endpoint returns 200
- [ ] `/api/v1/routes` shows all routes
- [ ] Analysis endpoints return 200 (not 404)
- [ ] Logs show `[PROVIDER]` messages with correct provider
- [ ] No "API_KEY not found" errors in logs

## Troubleshooting Commands

If you have Railway CLI installed:
```bash
# Check environment variables
railway variables

# View logs
railway logs

# Trigger redeploy
railway up
```

## Expected Log Output

After successful deployment, you should see in logs:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:PORT
```

And when a request comes in:
```
[PROVIDER] Set LLM_PROVIDER='xai' (env now: xai)
[PROVIDER] Creating QueryRouterAgent (LLM_PROVIDER=xai)
[PROVIDER] Creating StreamingOrchestrator (LLM_PROVIDER=xai)
```

## Still Having Issues?

1. **Check Railway Service Settings**:
   - Root Directory: Should be your repo root (where Procfile is)
   - Build Command: Should be auto-detected or empty (uses Procfile)
   - Start Command: Should be auto-detected from Procfile

2. **Verify File Structure**:
   - `Procfile` in root ✅
   - `backend/api/server.py` exists ✅
   - `backend/routes/` exists ✅
   - `backend/data/part_database/` exists ✅

3. **Check Build Logs**:
   - Look for Python installation
   - Look for `pip install -r requirements.txt`
   - Look for any import errors during build

4. **Test Locally First**:
   ```bash
   cd backend/api
   python -m uvicorn server:app --host 0.0.0.0 --port 3001
   ```
   Then test: `curl http://localhost:3001/health`
   If this works locally, Railway should work too.

