# start.sh
#!/bin/bash

# Start the crawler in a loop to retry on failure
while true; do
    python crawler.py
    CRAWLER_PID=$!

    # Wait for 30 minutes (30 * 60 seconds)
    sleep 1800

    # Kill the crawler process to restart it
    kill $CRAWLER_PID
    
    # Optional: Wait a moment to ensure the process stops completely
    sleep 5
done &

# Start the uvicorn server
uvicorn app:app --host 0.0.0.0 --port 7860
