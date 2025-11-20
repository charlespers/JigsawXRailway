"""
Vercel Serverless Function for Component Analysis
Note: For full functionality, deploy Python backend separately (Railway/Render/Fly.io)
and set VITE_BACKEND_URL environment variable in Vercel.
"""

import json
import os

def handler(request):
    """
    Vercel serverless function handler.
    This is a proxy that forwards requests to the actual backend.
    For production, deploy the FastAPI backend separately.
    """
    # Get backend URL from environment (set in Vercel dashboard)
    backend_url = os.environ.get("BACKEND_URL", "http://localhost:3001")
    
    # Extract request body
    body = request.get("body", "{}")
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except:
            body = {}
    
    # For now, return instructions to deploy backend separately
    # In production, this would proxy to the backend URL
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
        "body": json.dumps({
            "message": "Backend should be deployed separately. Set BACKEND_URL in Vercel environment variables.",
            "backend_url": backend_url,
            "instructions": "Deploy Python backend to Railway/Render/Fly.io and set BACKEND_URL"
        })
    }
