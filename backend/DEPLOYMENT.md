# Deployment Guide

## Railway Deployment

The backend is configured to deploy on Railway using Nixpacks.

### Configuration Files

- `nixpacks.toml` - Nixpacks build configuration
- `railway.json` - Railway deployment settings
- `requirements.txt` - Python dependencies

### Build Process

1. **Setup Phase**: Installs Python 3.11
2. **Install Phase**:
   - Creates virtual environment at `/opt/venv`
   - Upgrades pip
   - Installs dependencies from `requirements.txt`
3. **Build Phase**: Runs build commands
4. **Start Phase**: Runs the FastAPI application

### Environment Variables

Set these in Railway dashboard (Variables tab):

#### Required:

- `XAI_API_KEY` - xAI API key for LLM (required for agent features)

#### Optional (have defaults):

- `LLM_PROVIDER` - LLM provider (default: `xai`)
- `CORS_ORIGINS` - CORS allowed origins (default: `*` for all)
  - **For production**: Set to your frontend domain(s), comma-separated
  - Example: `https://jigsawxrailway-frontend.up.railway.app,https://yourdomain.com`
  - **For development**: Leave as `*` or don't set (defaults to allow all)
- `LOG_LEVEL` - Logging level (default: `INFO`)
  - Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`
  - **For production**: Use `INFO` (default) or `WARNING`
  - **For debugging**: Use `DEBUG` (more verbose)

#### Automatically Set (don't set manually):

- `PORT` - **Railway automatically sets this** - don't set manually!
  - The app reads `os.environ.get("PORT", 8000)` and Railway provides it

### Troubleshooting

**Issue**: `externally-managed-environment` error
**Solution**: The nixpacks.toml now creates a virtual environment to avoid this issue.

**Issue**: Module not found errors
**Solution**: Ensure all imports use `app.` prefix (e.g., `from app.api.routes import router`)

**Issue**: CORS errors
**Solution**: Set `CORS_ORIGINS` environment variable to your frontend domain(s)

### Local Testing

Test the deployment locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python -m app.main
```

The app will start on `http://localhost:8000`

### Health Check

After deployment, verify the service:

```bash
curl https://your-railway-app.up.railway.app/health
```

Should return: `{"status": "ok", "version": "2.0.0"}`
