# Deployment Guide - YC Demo

## Quick Deploy

### Option 1: Streamlit Cloud (Recommended)

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app"
4. Select your repository
5. Main file: `Home.py`
6. Add Secret: `XAI_API_KEY = "your_key"`
7. Click "Deploy"

**URL:** `https://your-app.streamlit.app`

---

### Option 2: Railway

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Add environment variable:
   ```
   XAI_API_KEY=your_key_here
   ```
5. Railway auto-detects Dockerfile and deploys

**URL:** `https://your-app.railway.app`

---

### Option 3: Heroku

```bash
# Install Heroku CLI
brew install heroku/brew/heroku  # macOS
# or download from heroku.com

# Login
heroku login

# Create app
heroku create your-app-name

# Set config
heroku config:set XAI_API_KEY="your_key"

# Add buildpack
heroku buildpacks:set heroku/python

# Deploy
git push heroku main

# Open
heroku open
```

**URL:** `https://your-app-name.herokuapp.com`

---

### Option 4: Docker (Self-Hosted)

```bash
# Build image
docker build -t yc-demo .

# Run container
docker run -d \
  -p 8501:8501 \
  -e XAI_API_KEY="your_key" \
  --name yc-demo \
  yc-demo

# View logs
docker logs -f yc-demo

# Stop
docker stop yc-demo
```

**URL:** `http://localhost:8501` or your server IP

---

### Option 5: DigitalOcean App Platform

1. Go to [cloud.digitalocean.com/apps](https://cloud.digitalocean.com/apps)
2. Click "Create App"
3. Connect GitHub repository
4. Choose "Dockerfile" as build method
5. Add environment variable: `XAI_API_KEY`
6. Click "Create Resources"

**URL:** `https://your-app.ondigitalocean.app`

---

### Option 6: Fly.io

```bash
# Install flyctl
brew install flyctl  # macOS
# or curl -L https://fly.io/install.sh | sh

# Login
flyctl auth login

# Launch app
flyctl launch

# Set secret
flyctl secrets set XAI_API_KEY="your_key"

# Deploy
flyctl deploy

# Open
flyctl open
```

**URL:** `https://your-app.fly.dev`

---

## Environment Variables

All deployment methods require:

```bash
XAI_API_KEY="your_xai_api_key_here"
```

Optional variables:

```bash
XAI_MODEL="grok-beta"              # XAI model to use
XAI_TEMPERATURE="0.3"              # Reasoning temperature (0-1)
MAX_COMPONENTS="10"                # Max components per simulation
SIMULATION_TIMEOUT="30"            # Timeout in seconds
DEBUG_MODE="false"                 # Enable debug logging
DEPLOYMENT_ENV="production"        # local|staging|production
PORT="8501"                        # Server port (auto-set by most platforms)
```

---

## Custom Domain

### Streamlit Cloud

1. Go to app settings
2. Click "Custom domain"
3. Add your domain (e.g., `sim.yourdomain.com`)
4. Update DNS: CNAME pointing to Streamlit

### Heroku

```bash
heroku domains:add sim.yourdomain.com
heroku domains:info sim.yourdomain.com
# Add DNS record shown
```

### Railway

1. Go to app settings
2. Click "Generate Domain" or "Add Custom Domain"
3. Update DNS with CNAME

---

## Scaling

### Streamlit Cloud
- Automatic scaling
- 1GB RAM per app
- Unlimited viewers

### Railway
- Configure in settings:
  ```
  Replicas: 2-10
  RAM: 512MB-4GB
  CPU: 0.5-2 cores
  ```

### Heroku
```bash
# Scale dynos
heroku ps:scale web=2

# Upgrade dyno type
heroku ps:type performance-m
```

### Docker (Manual Scaling)
```bash
# Run multiple containers with load balancer
docker run -d -p 8501:8501 -e XAI_API_KEY="key" yc-demo
docker run -d -p 8502:8501 -e XAI_API_KEY="key" yc-demo
# Configure nginx/traefik for load balancing
```

---

## Monitoring

### Health Checks

Built-in healthcheck: `/_stcore/health`

### Logs

**Streamlit Cloud:** View in dashboard  
**Heroku:** `heroku logs --tail`  
**Railway:** View in dashboard  
**Docker:** `docker logs -f container_name`

### Metrics

Monitor:
- Response time
- API call rate (XAI)
- Memory usage
- Error rate

---

## Security

### API Key Protection

- NEVER commit `XAI_API_KEY` to git
- Use environment variables only
- Rotate keys regularly

### Rate Limiting

XAI API has rate limits. For production:
1. Implement caching
2. Queue requests
3. Add retry logic with backoff

### HTTPS

All recommended platforms provide free SSL certificates.

---

## Cost Estimation

### Streamlit Cloud
- **Free tier:** 1 private app
- **Pro:** $40/month (3 apps)
- **Teams:** $250/month (unlimited)

### Railway
- **Free:** $5/month credit
- **Pay-as-you-go:** ~$0.000463/GB-second

### Heroku
- **Eco:** $5/month (1 dyno)
- **Basic:** $7/month (1 dyno)
- **Standard:** $25-50/month

### DigitalOcean
- **Basic:** $5/month (512MB RAM)
- **Pro:** $12/month (1GB RAM)

### Fly.io
- **Free tier:** 3 shared CPUs, 256MB RAM
- **Paid:** $1.94/month per 256MB RAM

**Plus XAI API costs:**
- Grok: $5 per 1M tokens
- Estimate: $0.01-0.50 per simulation

---

## Troubleshooting

### Deployment fails

**Check:**
1. `XAI_API_KEY` is set
2. `requirements.txt` is up to date
3. Python version is 3.12+ (or 3.10+)
4. Dockerfile builds locally

### App crashes

**Check logs for:**
- Missing environment variables
- XAI API quota exceeded
- Memory limits exceeded
- Timeout errors

### Slow performance

**Solutions:**
1. Reduce `SIMULATION_TIMEOUT`
2. Limit `MAX_COMPONENTS`
3. Lower `XAI_TEMPERATURE`
4. Cache agent responses
5. Upgrade server tier

---

## Production Checklist

- [ ] `XAI_API_KEY` set in environment
- [ ] All dependencies in `requirements.txt`
- [ ] `.gitignore` includes `.env` and `venv/`
- [ ] Health checks enabled
- [ ] Logging configured
- [ ] Error handling tested
- [ ] Rate limiting implemented
- [ ] HTTPS enabled
- [ ] Custom domain configured (optional)
- [ ] Monitoring set up
- [ ] Backup plan for API key rotation

---

## Support

For deployment issues:
1. Check platform-specific docs
2. Review error logs
3. Test locally first
4. Verify XAI API quota

---

**Built for Y Combinator | Production-Ready | Deploy Anywhere**

