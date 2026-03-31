#!/bin/bash
# Start ngrok tunnel for port 3000 (frontend)
if ! command -v ngrok &> /dev/null; then
    echo "ngrok could not be found. Please install it first."
    exit 1
fi

# Check if authtoken is configured
if ! ngrok config check &> /dev/null; then
    echo "Warning: ngrok authtoken might not be configured. Run 'ngrok config add-authtoken <TOKEN>'."
fi

echo "Starting ngrok http 3000..."
ngrok http 3000 > ngrok.log 2>&1 &
echo "ngrok started in background. Check ngrok.log for details."
echo "Public URL:"
sleep 5
grep "url=" ngrok.log | cut -d "=" -f 2
