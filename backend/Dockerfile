FROM python:3.11-slim

# Work inside /app (this corresponds to the backend service root)
WORKDIR /app

# Copy the backend service (Railway project root should be this backend folder)
COPY . /app

# Install Python dependencies for the backend
RUN pip install --no-cache-dir -r requirements.txt

# Default port; Railway will override PORT env var
ENV PORT=3001

EXPOSE 3001

# Match your desired start command: `cd api && python -m uvicorn server:app --host 0.0.0.0 --port $PORT`
CMD ["sh", "-c", "cd api && python -m uvicorn server:app --host 0.0.0.0 --port ${PORT}"]


