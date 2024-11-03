#!/bin/bash

# Start the uvicorn server in the background
uvicorn app:app --host 0.0.0.0 --port 7860 &
python3 ./src/introlix_api/app/algolia.py &

# Infinite loop to restart the crawler every 30 minutes
while true; do
    # Start the crawler in the background
    python3 crawler.py &
    
    # Wait 30 minutes before restarting
    sleep 1800
    
    # Kill the crawler process to restart it
    kill $!
done