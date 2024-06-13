#!/bin/bash

# Load secrets from .secrets file
source ./.secrets

# Variables
STACK_NAME="backend"
STACK_FILE_PATH="$HOME/Workspace/evoflow-monitor/r-pi/docker/backend_stack.yml"

# Check if the stack file exists and is readable
if [ ! -f "$STACK_FILE_PATH" ]; then
  echo "File $STACK_FILE_PATH does not exist."
  exit 1
elif [ ! -r "$STACK_FILE_PATH" ]; then
  echo "File $STACK_FILE_PATH is not readable."
  exit 1
fi

# Authenticate
echo "Authenticating"
JWT=$(curl -s -X POST "https://${PORTAINER_HOST}:${PORTAINER_PORT}/api/auth" \
  -k \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"${USERNAME}\", \"password\": \"${PASSWORD}\"}" | jq -r '.jwt')

# Check if JWT is empty
if [ -z "$JWT" ]; then
  echo "Authentication failed."
  exit 1
fi

echo "JWT token obtained: $JWT"

# Upload and deploy stack
echo "Uploading File"
RESPONSE=$(curl --location "https://${PORTAINER_HOST}:${PORTAINER_PORT}/api/stacks/create/standalone/file" \
--insecure \
--header "Authorization: Bearer $JWT" \
--form "Name=${STACK_NAME}" \
--form "file=@${STACK_FILE_PATH}" \
--form "endpointId=${ENDPOINT_ID}")

# Check if RESPONSE is empty
if [ -z "$RESPONSE" ]; then
  echo "Stack upload failed."
  exit 1
fi

echo "Response from server: $RESPONSE"

# Extract Stack ID
echo "Extracting Stack ID"
STACK_ID=$(echo $RESPONSE | jq -r '.Id')

# Check if STACK_ID is empty
if [ -z "$STACK_ID" ]; then
  echo "Failed to extract Stack ID."
  exit 1
fi

echo "Stack $STACK_NAME deployed with ID $STACK_ID"

