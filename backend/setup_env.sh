#!/bin/bash
# Setup script for OpenAI API key

echo "Setting up OpenAI API key..."

# Set the API key as an environment variable for current session
export OPENAI_API_KEY='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'

echo "✓ OPENAI_API_KEY has been set for this session"
echo ""
echo "To make this permanent, add this line to your ~/.zshrc or ~/.bashrc:"
echo "export OPENAI_API_KEY='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"
echo ""
echo "Or run: source setup_env.sh before starting Streamlit"

