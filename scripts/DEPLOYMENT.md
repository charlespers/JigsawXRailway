# Deployment Guide

## Overview

This application consists of:

1. **Frontend**: React/Vite application (deploys to Vercel)
2. **Backend**: Python FastAPI server (deploy separately)

## Frontend Deployment (Vercel)

### Prerequisites

- Vercel account
- GitHub repository

### Steps

1. **Connect Repository to Vercel**

   - Go to [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Vercel will auto-detect the frontend configuration

2. **Set Environment Variables**
   In Vercel dashboard → Project Settings → Environment Variables:

   ```
   VITE_BACKEND_URL=https://your-backend-url.railway.app
   ```

3. **Deploy**
   - Vercel will automatically deploy on push to main branch
   - Or manually trigger deployment from dashboard

## Backend Deployment Options

### Option 1: Railway (Recommended for Quick Demo)

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Set root directory to `charles_agentPCB_folder`
5. Add environment variables:
   ```
   OPENAI_API_KEY=your_openai_key
   XAI_API_KEY=your_xai_key
   LLM_PROVIDER=openai
   PORT=3001
   ```
6. Railway will auto-detect Python and install dependencies
7. Set start command: `cd api && python -m uvicorn server:app --host 0.0.0.0 --port $PORT`
8. Copy the generated URL (e.g., `https://your-app.railway.app`)
9. Add this URL to Vercel's `VITE_BACKEND_URL` environment variable

### Option 2: Render

1. Go to [render.com](https://render.com)
2. Click "New" → "Web Service"
3. Connect GitHub repository
4. Configure:
   - **Root Directory**: `charles_agentPCB_folder`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `cd api && uvicorn server:app --host 0.0.0.0 --port $PORT`
   - **Port**: 3001
5. Add environment variables (same as Railway)
6. Copy the URL and add to Vercel's `VITE_BACKEND_URL`

### Option 3: Fly.io

```bash
# Install flyctl
brew install flyctl  # macOS

# Login
flyctl auth login

# Create app
flyctl launch

# Set secrets
flyctl secrets set OPENAI_API_KEY="your_key"
flyctl secrets set XAI_API_KEY="your_key"
flyctl secrets set LLM_PROVIDER="openai"

# Deploy
flyctl deploy
```

### Option 4: Local Development

For local development, run both servers:

**Terminal 1 - Backend:**

```bash
cd charles_agentPCB_folder
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd api
python -m uvicorn server:app --reload --port 3001
```

**Terminal 2 - Frontend:**

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_BACKEND_URL=http://localhost:3001` in `.env` file.

## Environment Variables

### Frontend (Vercel)

- `VITE_BACKEND_URL`: Backend API URL (required)

### Backend (Railway/Render/Fly.io)

- `OPENAI_API_KEY`: OpenAI API key (required if using OpenAI)
- `XAI_API_KEY`: XAI API key (required if using XAI)
- `LLM_PROVIDER`: `openai` or `xai` (default: `openai`)
- `PORT`: Server port (default: 3001)

## Testing Deployment

1. **Test Backend Health**

   ```bash
   curl https://your-backend-url.railway.app/health
   ```

   Should return: `{"status":"ok"}`

2. **Test Frontend**
   - Visit your Vercel URL
   - Navigate to `/demo/auth`
   - Login with username: `demo`, password: `demo`
   - Test component analysis

## Troubleshooting

### Frontend can't connect to backend

- Check `VITE_BACKEND_URL` is set correctly in Vercel
- Verify backend is running and accessible
- Check CORS settings in backend (should allow all origins for demo)

### Backend errors

- Check environment variables are set
- Verify API keys are valid
- Check logs in Railway/Render dashboard

### SSE streaming not working

- Ensure backend supports Server-Sent Events
- Check network tab in browser DevTools
- Verify backend URL is correct

## Production Considerations

For production deployment:

1. Set specific CORS origins (not `*`)
2. Add rate limiting
3. Implement authentication
4. Set up monitoring/logging
5. Use environment-specific API keys
6. Enable HTTPS (automatic on most platforms)
