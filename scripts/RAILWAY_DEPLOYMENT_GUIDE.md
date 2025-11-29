# Railway Deployment Guide

## Step-by-Step Railway Configuration

### 1. Environment Variables

Go to your Railway project → **Variables** tab and add these:

#### Required Variables:
```
LLM_PROVIDER=xai
XAI_API_KEY=your_xai_api_key_here
```

**OR** if using OpenAI:
```
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
```

#### Optional (but recommended):
```
XAI_MODEL=grok-3
XAI_TEMPERATURE=0.3
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TEMPERATURE=0.3
```

### 2. Verify Deployment Structure

Ensure your Railway deployment includes:
- ✅ All files in `backend/`
- ✅ All files in `data/part_database/` (all JSON files)
- ✅ `routes/` directory with all route modules
- ✅ `agents/` directory with all agent files

### 3. Check Build Configuration

**If using Docker:**
- Ensure Dockerfile is in the correct location
- Verify the build context includes all necessary files

**If using Railway's buildpack:**
- Ensure `requirements.txt` or `pyproject.toml` is present
- Verify Python version is compatible

### 4. Verify Routes After Deployment

Once deployed, test these endpoints:

#### Health Check:
```bash
curl https://your-railway-url.railway.app/health
```
**Expected**: `{"status": "healthy", "version": "1.0.0", ...}`

#### Route List:
```bash
curl https://your-railway-url.railway.app/api/v1/routes
```
**Expected**: JSON list of all registered routes including `/api/v1/analysis/*`

#### Test Analysis Endpoint:
```bash
curl -X POST https://your-railway-url.railway.app/api/v1/analysis/validation \
  -H "Content-Type: application/json" \
  -d '{"bom_items": [{"part_data": {"id": "test"}, "quantity": 1}], "connections": []}'
```
**Expected**: Should return 200 (not 404)

### 5. Check Logs

In Railway dashboard → **Deployments** → Click on latest deployment → **View Logs**

Look for:
- ✅ `[PROVIDER] Set LLM_PROVIDER='xai'` messages
- ✅ Route registration messages
- ✅ Any import errors
- ✅ Any 404 errors (should not appear)

### 6. Common Issues & Fixes

#### Issue: Routes return 404
**Possible Causes:**
1. Routes not included in deployment
2. FastAPI app not starting correctly
3. Port configuration issue

**Fix:**
- Check Railway logs for startup errors
- Verify `api/server.py` is being executed
- Check that `routes/__init__.py` is included
- Ensure port is set correctly (Railway auto-assigns PORT env var)

#### Issue: Provider errors persist
**Possible Causes:**
1. Environment variables not set
2. Variables set but not applied to running service
3. Wrong variable names

**Fix:**
- Double-check variable names (case-sensitive)
- Redeploy after setting variables
- Check logs for `[PROVIDER]` messages to see what provider is being used

#### Issue: Database not found
**Possible Causes:**
1. `data/part_database/` files not included in deployment
2. Path resolution issue

**Fix:**
- Verify all JSON files in `data/part_database/` are in the deployment
- Check logs for "File not found" errors
- Verify relative paths are correct

### 7. Redeploy After Changes

After setting environment variables or making code changes:
1. Go to Railway dashboard
2. Click **Deploy** or trigger a new deployment
3. Wait for build to complete
4. Test endpoints again

### 8. Quick Verification Script

Create a test script to verify everything works:

```bash
#!/bin/bash
BASE_URL="https://your-railway-url.railway.app"

echo "Testing Health Check..."
curl -s "$BASE_URL/health" | jq .

echo "\nTesting Routes..."
curl -s "$BASE_URL/api/v1/routes" | jq '.routes | length'

echo "\nTesting Analysis Endpoint..."
curl -s -X POST "$BASE_URL/api/v1/analysis/validation" \
  -H "Content-Type: application/json" \
  -d '{"bom_items": [{"part_data": {"id": "test"}, "quantity": 1}], "connections": []}' \
  | jq .
```

## Expected Results

After proper configuration:
- ✅ Health check returns 200
- ✅ Route list shows 9 analysis routes
- ✅ Analysis endpoints return 200 (not 404)
- ✅ Provider errors should not occur
- ✅ Parts are found from database (check logs)

## If Issues Persist

1. **Check Railway Logs**: Look for startup errors, import errors, or route registration issues
2. **Verify File Structure**: Ensure all files are included in deployment
3. **Test Locally First**: Run the server locally to verify routes work
4. **Check Port Configuration**: Railway uses `PORT` environment variable automatically

## Contact Points

If routes still return 404 after following this guide:
- Check Railway deployment logs for errors
- Verify the FastAPI app is starting correctly
- Ensure `app.include_router(api_router)` is being executed
- Check that no errors occur during route registration

