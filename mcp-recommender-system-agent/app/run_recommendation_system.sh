#!/bin/bash

IMAGE_NAME="recommendation-system"

echo "🚀 Building Docker image: $IMAGE_NAME"
docker build -t $IMAGE_NAME .

echo "⏳ Waiting for a container from image '$IMAGE_NAME' to start running..."

# Poll every second until a container is running with the given image
while true; do
    CONTAINER_ID=$(docker ps --filter "ancestor=$IMAGE_NAME" --format "{{.ID}}")
    if [ ! -z "$CONTAINER_ID" ]; then
        echo "✅ Container is running: $CONTAINER_ID"
        echo "📋 Following logs..."
        docker logs -f $CONTAINER_ID
        break
    fi
    sleep 1
done
