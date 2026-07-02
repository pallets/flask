#!/bin/bash
set -e

IMAGE_NAME="omega/flask-tutorial:v1"
CONTAINER_NAME="flask-tutorial"
PORT=5000

# 1. Check Docker is installed
if ! command -v docker &> /dev/null
then
    echo "Docker is not installed. Please install Docker and try again."
    exit 1
fi

# 2. Idempotency: remove existing container with the same name, if any
if [ "$(docker ps -aq -f name=^${CONTAINER_NAME}$)" ]; then
    echo "Existing container '${CONTAINER_NAME}' found. Stopping and removing..."
    docker stop "${CONTAINER_NAME}" > /dev/null 2>&1
    docker rm "${CONTAINER_NAME}" > /dev/null 2>&1
fi

# 3. Build the Docker image
echo "Building Docker image: ${IMAGE_NAME}..."
docker build -t "${IMAGE_NAME}" .

# 4. Run the container
echo "Starting container..."
CONTAINER_ID=$(docker run -d -p ${PORT}:${PORT} --name "${CONTAINER_NAME}" "${IMAGE_NAME}")

# 5. Display deployment info
echo ""
echo "Deployment successful!"
echo "-----------------------------------"
echo "Container Name : ${CONTAINER_NAME}"
echo "Container ID   : ${CONTAINER_ID:0:12}"
echo "Image Name     : ${IMAGE_NAME}"
echo "Application URL: http://localhost:${PORT}"
echo "-----------------------------------"