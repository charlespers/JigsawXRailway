#!/bin/bash
# Start script for Railway deployment
# Ensures PORT environment variable is used correctly

PORT=${PORT:-3000}
echo "Starting Express server on port $PORT"
node server.js

