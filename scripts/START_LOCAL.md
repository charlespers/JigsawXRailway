# Local Development Setup

## Quick Start

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (if not exists)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
cd api
python -m uvicorn server:app --reload --port 3001
```

Backend will run on: `http://localhost:3001`

### 2. Frontend Setup

Open a new terminal:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if not already installed)
npm install

# Start development server
npm run dev
```

Frontend will run on: `http://localhost:5173` (or similar Vite port)

### 3. Access the Demo

1. Open browser to frontend URL (usually `http://localhost:5173`)
2. Navigate to `/demo/auth`
3. Login with:
   - Username: `demo`
   - Password: `demo`
4. Start using the component analysis tool!

## Environment Variables

### Backend (.env in backend/)
- `LLM_PROVIDER`: `openai` or `xai` (default: `openai`)
- `OPENAI_API_KEY`: Your OpenAI API key
- `XAI_API_KEY`: Your XAI API key

### Frontend (.env in frontend/)
- `VITE_BACKEND_URL`: Backend API URL (default: `http://localhost:3001`)

## Testing the Integration

1. **Test Provider Selection**
   - Select OpenAI or XAI from dropdown in chat
   - Send a query like "temperature sensor with wifi and 5V-USBC"
   - Verify components are selected in real-time

2. **Test BOM Editing**
   - After components are selected, edit quantities
   - Add notes to parts
   - Remove parts if needed

3. **Test Export**
   - Click "Export CSV" or "Export Excel"
   - Verify file downloads with correct data

4. **Test Settings**
   - Click settings icon (top-right)
   - Change backend URL or default provider
   - Save and verify changes persist

## Troubleshooting

### Backend won't start
- Check Python version (3.10+ required)
- Verify virtual environment is activated
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify .env file exists and has correct API keys

### Frontend can't connect to backend
- Verify backend is running on port 3001
- Check `VITE_BACKEND_URL` in frontend/.env
- Check browser console for CORS errors
- Verify backend CORS settings allow localhost

### API calls failing
- Check API keys are valid in backend .env
- Verify LLM_PROVIDER is set correctly
- Check backend logs for error messages
- Test backend health endpoint: `curl http://localhost:3001/health`

### Components not appearing
- Check browser console for errors
- Verify SSE streaming is working (check Network tab)
- Check backend logs for component selection events

## Development Tips

- Backend auto-reloads on code changes (--reload flag)
- Frontend hot-reloads on code changes (Vite default)
- Use browser DevTools to inspect SSE events
- Check backend terminal for agent reasoning logs

