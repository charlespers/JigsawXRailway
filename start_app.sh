#!/bin/bash
# Quick script to start the YC Demo app

cd "$(dirname "$0")"
source venv/bin/activate

# Check if XAI_API_KEY is set
if [ -z "$XAI_API_KEY" ]; then
    echo "❌ XAI_API_KEY environment variable not set!"
    echo "Please set it with: export XAI_API_KEY='your_grok_api_key_here'"
    exit 1
fi

echo "🚀 Starting YC Demo..."
echo "📱 App will be available at: http://localhost:8501"
echo "🛑 Press Ctrl+C to stop"

streamlit run Home.py --server.headless true --server.port 8501
