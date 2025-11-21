#!/bin/bash
# Start script for Railway deployment
# Ensures PORT environment variable is used correctly

PORT=${PORT:-3000}
echo "Starting serve on port $PORT"
npx serve -s dist -l $PORT

