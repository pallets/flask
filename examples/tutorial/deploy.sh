#!/bin/bash

IMAGE_NAME="flaskr-tutorial"
CONTAINER_NAME="flaskr-container"

echo "Building Docker image..."
docker build -t $IMAGE_NAME .

echo "Stopping old container..."
docker stop $CONTAINER_NAME 2>/dev/null
docker rm $CONTAINER_NAME 2>/dev/null

echo "Starting new container..."
docker run -d --name $CONTAINER_NAME -p 5000:5000 $IMAGE_NAME

echo "Initializing database..."
docker exec $CONTAINER_NAME flask --app flaskr init-db

echo ""
echo "Deployment Successful!"
echo "Container: $CONTAINER_NAME"
echo "Image: $IMAGE_NAME"
echo "URL: http://localhost:5000"
