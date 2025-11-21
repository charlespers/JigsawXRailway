# Railway 502 Error Troubleshooting Guide

## Current Implementation Status

✅ **Server Configuration**: Matches Railway's Express example exactly
- Listening on `0.0.0.0` (all interfaces) ✓
- Using `process.env.PORT` ✓
- Express server serving static files ✓

## Step-by-Step Debugging

### 1. Check Railway Deployment Logs

Go to: **Frontend Service → Deployments → Latest Deployment → View Logs**

**Look for these messages:**
```
Starting server...
PORT: [number]
DIST_DIR: /app/dist
Dist directory exists: true
✓ Server running on http://0.0.0.0:[PORT]
✓ Serving static files from /app/dist
✓ Ready to accept connections
```

**If you DON'T see these messages:**
- Server is crashing before it can start
- Check for error messages above the "Starting server..." line
- Common issues:
  - `dist` folder doesn't exist (build failed)
  - Express import error
  - Syntax error in server.js

**If you DO see these messages:**
- Server is starting correctly
- Issue is likely with Railway's target port configuration (see step 2)

### 2. Check Target Port Configuration

Go to: **Frontend Service → Settings → Networking → Public Networking**

**Check your domain's target port:**
1. Find your domain (e.g., `jigsawxrailway-frontend.up.railway.app`)
2. Click the **edit icon** (pencil) next to the domain
3. Check the **Target Port** value
4. **This MUST match the PORT your server is listening on**

**How to find the correct PORT:**
- Check the Railway logs for: `PORT: [number]`
- Or check the logs for: `✓ Server running on http://0.0.0.0:[PORT]`
- The PORT number shown there is what Railway assigned

**Fix:**
- If target port is wrong (e.g., 3000 but server is on 8080):
  - Click edit icon
  - Change target port to match the PORT from logs
  - Save

### 3. Verify Build Succeeded

In Railway logs, look for:
```
✓ built in X.XXs
```

**If build failed:**
- Check for TypeScript errors
- Check for missing dependencies
- Verify `npm run build` completes successfully

### 4. Verify Express is Installed

In Railway logs, during `npm install` phase, you should see:
```
+ express@4.18.2
```

**If Express is missing:**
- Check `package.json` has `express` in dependencies
- Verify it's not in `devDependencies` (should be in `dependencies`)

### 5. Check Service Health

Go to: **Frontend Service → Metrics**

**Check:**
- Is the service running? (should show "Running")
- CPU/Memory usage (should be low for a static site)
- Any crashes or restarts?

## Common Issues and Solutions

### Issue: Server logs show "ERROR: dist directory not found"
**Solution:** Build failed. Check build logs for TypeScript/build errors.

### Issue: Server logs show "Port X is already in use"
**Solution:** Unlikely on Railway, but if it happens, Railway should handle it automatically.

### Issue: Server starts but target port is wrong
**Solution:** Update target port in Railway domain settings to match the PORT from logs.

### Issue: No server logs at all
**Solution:** 
- Check if start command is correct: `node server.js`
- Verify `server.js` exists in `frontend/` directory
- Check Railway is using the correct root directory (`frontend`)

## Verification Checklist

Before reporting issues, verify:

- [ ] Root Directory is set to `frontend` in Railway settings
- [ ] Start Command is `node server.js` (or Railway auto-detects it)
- [ ] Build completes successfully (`✓ built in X.XXs`)
- [ ] Server logs show `✓ Server running on http://0.0.0.0:[PORT]`
- [ ] Target port in domain settings matches the PORT from logs
- [ ] Express is in `dependencies` (not `devDependencies`)
- [ ] `server.js` exists in `frontend/` directory

## Still Having Issues?

If all the above checks pass but you still get 502 errors:

1. **Check Railway Status**: https://status.railway.com
2. **Try Redeploying**: Sometimes a fresh deployment fixes issues
3. **Check Railway Discord**: https://discord.gg/railway
4. **Contact Railway Support**: Include your service logs and this checklist

