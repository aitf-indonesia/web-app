#!/bin/bash

# Test script for RunPod log integration
# This script demonstrates how to:
# 1. Start a crawler job
# 2. Get the job_id
# 3. Send logs to that job

BACKEND_URL="http://18.140.62.254"
# Get auth token (replace with your actual token)
# You can get this from browser localStorage after login
AUTH_TOKEN="your-auth-token-here"

echo "=== RunPod Log Integration Test ==="
echo ""

# Step 1: Start a crawler job
echo "Step 1: Starting a crawler job..."
RESPONSE=$(curl -s -X POST "${BACKEND_URL}/api/crawler/start" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -d '{
    "domain_count": 5,
    "keywords": ["test keyword"]
  }')

echo "Response: $RESPONSE"
echo ""

# Extract job_id from response
JOB_ID=$(echo $RESPONSE | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$JOB_ID" ]; then
  echo "❌ Failed to start job or extract job_id"
  echo "Make sure you have a valid AUTH_TOKEN"
  exit 1
fi

echo "✅ Job started successfully!"
echo "Job ID: $JOB_ID"
echo ""

# Step 2: Send test logs
echo "Step 2: Sending test logs to job..."
echo ""

# Send multiple log messages
for i in {1..5}; do
  echo "Sending log $i/5..."
  curl -s -X POST "${BACKEND_URL}/api/crawler/log" \
    -H "Content-Type: application/json" \
    -d "{
      \"job_id\": \"${JOB_ID}\",
      \"message\": \"[INFO] Test log message $i from RunPod simulation\"
    }"
  echo ""
  sleep 1
done

echo ""
echo "✅ Test logs sent successfully!"
echo ""
echo "📋 Instructions:"
echo "1. Open the Domain Generator UI in your browser"
echo "2. You should see the test logs appearing in real-time"
echo "3. Job ID: $JOB_ID"
echo ""
echo "To view logs via API:"
echo "curl ${BACKEND_URL}/api/crawler/logs/${JOB_ID}"
