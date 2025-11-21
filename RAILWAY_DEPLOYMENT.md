# Railway Deployment Guide

Complete step-by-step guide for deploying the PCB Design Agent System to Railway.

## Overview

Railway will host both:
1. **Backend**: Python FastAPI server (`charles_agentPCB_folder/api/server.py`)
2. **Frontend**: React/Vite application (`frontend/`)

## Prerequisites

- GitHub account with your repository pushed
- Railway account ([railway.app](https://railway.app))
- OpenAI API key (or XAI API key)

## Step 1: Create Railway Account and Project

1. Go to [railway.app](https://railway.app)
2. Sign up/login with GitHub
3. Click **"New Project"**
4. Select **"Deploy from GitHub repo"**
5. Choose your repository (`yc_jigsaw_demo`)

## Step 2: Deploy Backend Service

### 2.1 Create Backend Service

1. In your Railway project, click **"+ New"** → **"GitHub Repo"**
2. Select the same repository
3. Railway will detect it's a Python project

### 2.2 Configure Backend Service

1. Click on the service to open settings
2. Go to **"Settings"** tab
3. Set **Root Directory**: `charles_agentPCB_folder`
4. Set **Start Command**: 
   ```
   cd api && python -m uvicorn server:app --host 0.0.0.0 --port $PORT
   ```
5. Railway will auto-detect Python and install from `requirements.txt`

### 2.3 Set Backend Environment Variables

1. Go to **"Variables"** tab in the backend service
2. Add the following environment variables:

   ```
   OPENAI_API_KEY=sk-proj-your-key-here
   XAI_API_KEY=your-xai-key-here
   LLM_PROVIDER=openai
   PORT=3001
   ```

   **Note**: Railway automatically sets `PORT` - you can use `$PORT` in your start command, but the default is fine.

3. Click **"Deploy"** or Railway will auto-deploy

### 2.4 Get Backend URL

1. Once deployed, go to **"Settings"** → **"Networking"**
2. Click **"Generate Domain"** to get a public URL
3. Copy the URL (e.g., `https://your-backend-production.up.railway.app`)
4. **Important**: Save this URL - you'll need it for the frontend

## Step 3: Deploy Frontend Service

### 3.1 Create Frontend Service

1. In the same Railway project, click **"+ New"** → **"GitHub Repo"**
2. Select the same repository again
3. Railway will detect it's a Node.js project

### 3.2 Configure Frontend Service

1. Click on the frontend service
2. Go to **"Settings"** tab
3. Set **Root Directory**: `frontend`
4. Railway will auto-detect:
   - **Build Command**: `npm run build` (or `yarn build`)
   - **Start Command**: `npx serve -s dist` (for static hosting)

### 3.3 Set Frontend Environment Variables

1. Go to **"Variables"** tab in the frontend service
2. Add:

   ```
   VITE_BACKEND_URL=https://your-backend-production.up.railway.app
   ```

   Replace `your-backend-production.up.railway.app` with your actual backend URL from Step 2.4

### 3.4 Configure Static Site Settings

1. In **"Settings"** → **"Deploy"**
2. Set **Output Directory**: `dist`
3. Railway will serve the built static files

### 3.5 Get Frontend URL

1. Go to **"Settings"** → **"Networking"**
2. Click **"Generate Domain"** for the frontend
3. Copy the URL (e.g., `https://your-frontend-production.up.railway.app`)

## Step 4: Update Backend CORS (If Needed)

The backend should already allow all origins (`allow_origins=["*"]`), but verify in `charles_agentPCB_folder/api/server.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For demo - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Step 5: Test Deployment

### 5.1 Test Backend

```bash
# Test health endpoint
curl https://your-backend-production.up.railway.app/health

# Should return: {"status":"ok"}
```

### 5.2 Test Frontend

1. Visit your frontend URL: `https://your-frontend-production.up.railway.app`
2. Navigate to `/demo/auth`
3. Login with:
   - Username: `demo`
   - Password: `demo`
4. Test component analysis with a query like: "temperature sensor with wifi and 5V USB-C"

## Step 6: Custom Domains (Optional)

### 6.1 Backend Custom Domain

1. In backend service → **"Settings"** → **"Networking"**
2. Click **"Custom Domain"**
3. Add your domain (e.g., `api.yourdomain.com`)
4. Follow Railway's DNS instructions

### 6.2 Frontend Custom Domain

1. In frontend service → **"Settings"** → **"Networking"**
2. Click **"Custom Domain"**
3. Add your domain (e.g., `app.yourdomain.com`)
4. Update `VITE_BACKEND_URL` to use your custom backend domain

## Troubleshooting

### Backend Not Starting

1. **Check Logs**: Railway dashboard → Service → **"Deployments"** → Click latest deployment → **"View Logs"**
2. **Common Issues**:
   - Missing environment variables → Check **"Variables"** tab
   - Python version mismatch → Railway auto-detects, but you can specify in `runtime.txt`:
     ```
     python-3.11
     ```
   - Import errors → Check `requirements.txt` includes all dependencies

### Frontend Can't Connect to Backend

1. **Check `VITE_BACKEND_URL`**: Must match your backend Railway URL exactly
2. **Check CORS**: Backend should allow all origins (already configured)
3. **Check Network Tab**: Open browser DevTools → Network → Look for failed requests
4. **Verify Backend is Running**: Test `/health` endpoint

### Build Failures

1. **Frontend Build Fails**:
   - Check Node version (Railway auto-detects)
   - Verify `package.json` has correct build script
   - Check logs for specific errors

2. **Backend Build Fails**:
   - Verify `requirements.txt` is in `charles_agentPCB_folder/`
   - Check Python version compatibility
   - Review error logs

### SSE Streaming Not Working

1. **Check Backend Logs**: Look for errors in component analysis
2. **Verify API Keys**: Ensure `OPENAI_API_KEY` or `XAI_API_KEY` is set correctly
3. **Test Backend Directly**: Use curl or Postman to test `/mcp/component-analysis` endpoint
4. **Check Browser Console**: Look for CORS or network errors

## Railway-Specific Files

### Optional: `railway.json` (for advanced configuration)

Create `railway.json` in project root:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "cd api && python -m uvicorn server:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Optional: `runtime.txt` (for Python version)

Create `charles_agentPCB_folder/runtime.txt`:

```
python-3.11
```

## Environment Variables Reference

### Backend Service

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `OPENAI_API_KEY` | Yes* | OpenAI API key | `sk-proj-...` |
| `XAI_API_KEY` | Yes* | XAI API key | `pCjyLomxl...` |
| `LLM_PROVIDER` | No | Provider to use | `openai` or `xai` |
| `PORT` | No | Server port (Railway sets automatically) | `3001` |

*At least one API key is required

### Frontend Service

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `VITE_BACKEND_URL` | Yes | Backend API URL | `https://backend.up.railway.app` |

## Cost Estimation

Railway pricing (as of 2024):
- **Free Tier**: $5 credit/month
- **Hobby Plan**: $5/month + usage
- **Pro Plan**: $20/month + usage

For this demo:
- Backend: ~$5-10/month (depending on usage)
- Frontend: ~$2-5/month (static hosting is cheap)

**Total**: ~$7-15/month for both services

## Production Checklist

Before going live:

- [ ] Set specific CORS origins (not `*`)
- [ ] Add rate limiting to backend
- [ ] Implement proper authentication (replace demo password)
- [ ] Set up monitoring/logging
- [ ] Use production API keys (separate from dev)
- [ ] Enable HTTPS (automatic on Railway)
- [ ] Set up custom domains
- [ ] Configure backup/restore
- [ ] Set up alerts for downtime

## Quick Reference Commands

### View Logs
- Railway Dashboard → Service → Deployments → View Logs

### Redeploy
- Railway Dashboard → Service → Deployments → Click "Redeploy"

### Update Environment Variables
- Railway Dashboard → Service → Variables → Add/Edit

### Check Service Status
- Railway Dashboard → Service → Overview

## Support

- Railway Docs: [docs.railway.app](https://docs.railway.app)
- Railway Discord: [discord.gg/railway](https://discord.gg/railway)
- Check logs in Railway dashboard for specific errors

