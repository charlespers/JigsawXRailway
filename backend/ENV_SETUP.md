# Environment Variables Setup Guide

## Quick Answer

### ✅ What You MUST Set:
1. **`XAI_API_KEY`** - Required for LLM features

### ⚙️ What You CAN Set (but have defaults):
1. **`CORS_ORIGINS`** - Only if you want to restrict CORS (default: allows all)
2. **`LOG_LEVEL`** - Only if you want different logging (default: INFO)

### ❌ What You Should NOT Set:
1. **`PORT`** - Railway sets this automatically!

---

## Detailed Explanation

### 1. PORT (Don't Set This!)

**Status**: ✅ Automatically handled by Railway

Railway automatically sets the `PORT` environment variable when your service starts. The code reads it like this:

```python
port = int(os.environ.get("PORT", 8000))  # Railway provides PORT automatically
```

**Action**: Do nothing - Railway handles it!

---

### 2. CORS_ORIGINS (Optional - Defaults to Allow All)

**Status**: ⚙️ Optional - defaults to `*` (allow all origins)

**Current Default**: `*` (allows requests from any origin)

**When to Set**:
- ✅ **Production**: Set to your frontend domain(s) for security
- ❌ **Development**: Can leave as default (`*`)

**How to Set**:
```
CORS_ORIGINS=https://jigsawxrailway-frontend.up.railway.app,https://yourdomain.com
```

**Examples**:
- Single frontend: `https://myapp.up.railway.app`
- Multiple frontends: `https://app1.com,https://app2.com`
- Development (allow all): Don't set, or set to `*`

**Action**: 
- For production: Set to your frontend URL(s)
- For development: Leave unset (defaults to `*`)

---

### 3. LOG_LEVEL (Optional - Defaults to INFO)

**Status**: ⚙️ Optional - defaults to `INFO`

**Current Default**: `INFO`

**Options**:
- `DEBUG` - Very verbose, shows everything (use for debugging)
- `INFO` - Normal logging (default, good for production)
- `WARNING` - Only warnings and errors
- `ERROR` - Only errors

**When to Set**:
- ✅ **Debugging issues**: Set to `DEBUG` temporarily
- ✅ **Production**: Use `INFO` (default) or `WARNING`
- ❌ **Normal operation**: Don't set (defaults to INFO)

**Action**: 
- For production: Leave unset (uses INFO)
- For debugging: Set to `DEBUG` temporarily

---

### 4. XAI_API_KEY (Required!)

**Status**: ✅ **MUST SET** - Required for LLM features

**What it is**: Your xAI API key for LLM-powered features

**How to Get**:
1. Sign up at https://x.ai
2. Get your API key from the dashboard
3. Set it in Railway Variables tab

**Action**: **MUST SET THIS** or agent features won't work!

---

## Railway Setup Steps

1. Go to your Railway project dashboard
2. Click on your backend service
3. Go to **"Variables"** tab
4. Click **"New Variable"**
5. Add:

   ```
   Name: XAI_API_KEY
   Value: your-xai-api-key-here
   ```

6. (Optional) Add CORS_ORIGINS if needed:
   ```
   Name: CORS_ORIGINS
   Value: https://your-frontend.up.railway.app
   ```

7. Railway will automatically redeploy when you add variables

---

## Summary Table

| Variable | Required? | Default | When to Set |
|----------|-----------|---------|-------------|
| `PORT` | ❌ No | Railway sets | Never - Railway handles it |
| `XAI_API_KEY` | ✅ Yes | None | Always - required for LLM |
| `CORS_ORIGINS` | ⚙️ Optional | `*` | Production - restrict to frontend |
| `LOG_LEVEL` | ⚙️ Optional | `INFO` | Debugging - set to DEBUG |

---

## Verification

After setting variables, check logs:

```bash
# Railway will show in logs:
# "CORS configured with origins: ['*']" (or your custom origins)
# "Log level: INFO" (or your custom level)
```

Test the API:
```bash
curl https://your-backend.up.railway.app/health
# Should return: {"status": "ok", "version": "2.0.0"}
```

