# Railway Troubleshooting - Routes Returning 404

## ✅ What's Working
- `/health` endpoint returns OK ✅
- Server is running ✅
- Routes are registered correctly in code ✅

## ❌ What's Not Working
- Analysis endpoints return 404 on Railway

## Diagnostic Steps

### Step 1: Check Route Registration on Railway

After your next deployment, check Railway logs for:
```
[ROUTES] Successfully included api_router. Total routes: X, Analysis routes: 9
[STARTUP] Application started. Total routes: X, Analysis routes: 9
```

**If you see:**
- `Analysis routes: 0` → Routes are NOT being registered
- `Failed to import api_router` → Import error
- No route logs at all → Routes module not loading

### Step 2: Test Route List Endpoint

After deployment, test:
```bash
curl https://your-railway-url.railway.app/api/v1/routes
```

**Expected response:**
```json
{
  "routes": [...],
  "total_routes": 40,
  "analysis_routes_count": 9,
  "analysis_routes": [
    "/api/v1/analysis/validation",
    "/api/v1/analysis/thermal",
    ...
  ],
  "health_check_works": true
}
```

**If `analysis_routes_count` is 0:**
- Routes are not being registered
- Check Railway logs for import errors
- Verify `routes/` directory is in deployment

### Step 3: Check Railway Logs for Errors

Look for these in Railway logs:

**Good signs:**
```
[ROUTES] Successfully imported api_router from routes module
[ROUTES] Successfully included api_router. Total routes: 40, Analysis routes: 9
[STARTUP] Application started. Total routes: 40, Analysis routes: 9
```

**Bad signs:**
```
[ROUTES] Failed to import api_router: ...
ModuleNotFoundError: No module named 'routes'
ImportError: cannot import name 'api_router'
[ROUTES] WARNING: No analysis routes found!
[STARTUP] CRITICAL: No analysis routes registered!
```

### Step 4: Verify File Structure on Railway

Railway should have these files:
```
/
├── Procfile
├── railway.json
└── backend/
    ├── api/
    │   └── server.py
    ├── routes/
    │   ├── __init__.py
    │   ├── analysis.py
    │   ├── design.py
    │   ├── parts.py
    │   └── export.py
    ├── agents/
    ├── data/
    │   └── part_database/
    └── ...
```

### Step 5: Check Railway Service Settings

1. **Root Directory**: Should be empty (`.` or blank) - Railway runs from repo root
2. **Build Command**: Should be auto-detected (uses `requirements.txt`)
3. **Start Command**: Should be auto-detected from `Procfile`

### Step 6: Force Rebuild

If routes still don't work:
1. Go to Railway → **Settings** → **Danger Zone**
2. Click **Clear Build Cache**
3. Click **Redeploy**

This forces Railway to rebuild everything from scratch.

## Quick Test Commands

After deployment, run these to diagnose:

```bash
# 1. Health check (should work)
curl https://your-railway-url.railway.app/health

# 2. Route list (should show analysis routes)
curl https://your-railway-url.railway.app/api/v1/routes | jq '.analysis_routes_count'

# 3. Test analysis endpoint (should return 200, not 404)
curl -X POST https://your-railway-url.railway.app/api/v1/analysis/validation \
  -H "Content-Type: application/json" \
  -d '{"bom_items": [{"part_data": {"id": "test"}, "quantity": 1}], "connections": []}'
```

## Most Likely Causes

1. **Routes module not in deployment** (30% chance)
   - Fix: Verify `routes/` directory is committed to git
   - Check Railway build logs for missing files

2. **Import error preventing route registration** (40% chance)
   - Fix: Check Railway logs for import errors
   - Verify all dependencies in `requirements.txt`
   - Check for circular imports

3. **Working directory mismatch** (20% chance)
   - Fix: Check Railway Root Directory setting
   - Verify Procfile path is correct

4. **Routes registered but wrong path** (10% chance)
   - Fix: Check if Railway is proxying/rewriting paths
   - Verify route paths match frontend expectations

## Next Steps

1. **Check Railway logs** after next deployment
2. **Test `/api/v1/routes` endpoint** - this will tell you if routes are registered
3. **Share the output** of `/api/v1/routes` - this will help diagnose the issue

The code is correct - this is likely a Railway deployment configuration issue.

