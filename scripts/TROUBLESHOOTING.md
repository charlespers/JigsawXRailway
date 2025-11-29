# Troubleshooting Guide

## XAI API Key Issues

If you're getting an error like:
```
HTTP 400 - Incorrect API key provided: pC***7g
```

This means the XAI API key in your `.env` file is invalid or expired.

### How to Fix:

1. **Get a new XAI API key:**
   - Go to https://console.x.ai
   - Sign in or create an account
   - Navigate to API Keys section
   - Generate a new API key

2. **Update your `.env` file:**
   ```bash
   cd backend
   # Edit .env file and replace XAI_API_KEY with your new key
   XAI_API_KEY=your_new_key_here
   ```

3. **Restart the backend server:**
   ```bash
   # Stop the current server (Ctrl+C)
   # Then restart:
   cd api
   python -m uvicorn server:app --reload --port 3001
   ```

### Testing API Keys

You can test if your API keys are valid:

**Test OpenAI:**
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**Test XAI:**
```bash
curl https://api.x.ai/v1/models \
  -H "Authorization: Bearer $XAI_API_KEY"
```

If you get a 401 Unauthorized error, the API key is invalid.

## Provider Selection

The provider dropdown in the chat interface allows you to select between:
- **OpenAI**: Uses GPT models (requires OPENAI_API_KEY)
- **XAI (Grok)**: Uses Grok models (requires XAI_API_KEY)

**Note:** Make sure the corresponding API key is set in your `.env` file for the provider you want to use.

## Common Issues

### 1. "API key not found" error
- Check that `.env` file exists in `backend/`
- Verify the environment variable names are correct (no typos)
- Restart the backend server after changing `.env`

### 2. Provider not switching
- Clear browser localStorage: Open DevTools → Application → Local Storage → Clear
- Or manually set provider in Settings panel (top-right gear icon)

### 3. Backend not connecting
- Verify backend is running on port 3001
- Check `VITE_BACKEND_URL` in `frontend/.env` matches backend URL
- Check browser console for CORS errors

### 4. Components not appearing
- Check backend logs for errors
- Verify API keys are valid
- Check browser Network tab for SSE stream events

