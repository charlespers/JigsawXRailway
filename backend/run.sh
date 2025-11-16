#!/bin/bash

# Production run script for YC Demo

echo "AI PCB Simulator - YC Demo"
echo "============================"
echo ""

# Check for XAI API key
if [ -z "$XAI_API_KEY" ]; then
    echo "ERROR: XAI_API_KEY environment variable is required"
    echo ""
    echo "This simulator uses XAI for component reasoning."
    echo "Set it with: export XAI_API_KEY='your_key'"
    echo ""
    exit 1
fi

echo "Configuration:"
echo "  XAI API Key: SET"
echo "  Python: $(python3 --version)"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3.12 -m venv venv || python3 -m venv venv
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ""
echo "Starting simulator..."
echo "Open browser to: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run Streamlit
streamlit run Home.py
