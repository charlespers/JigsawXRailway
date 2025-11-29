FROM python:3.11-slim

# Work inside /app (this will be the /backend root when Railway root is set to /backend)
WORKDIR /app

# Copy backend code (everything under /backend in your repo)
COPY . /app

# Install Python dependencies for the backend
RUN pip install --no-cache-dir -r requirements.txt

# Default port; Railway will override PORT env var
ENV PORT=3001

EXPOSE 3001

# Match your desired start command: `cd api && python -m uvicorn server:app --host 0.0.0.0 --port $PORT`
CMD ["sh", "-c", "cd api && python -m uvicorn server:app --host 0.0.0.0 --port ${PORT}"]


