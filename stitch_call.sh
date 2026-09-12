#!/bin/bash
export HTTPS_PROXY=http://127.0.0.1:10808

PROJECT="projects/9174607280697972367"
API="https://stitch.googleapis.com/mcp"
KEY="AQ.Ab8RN6IZI0NZNSIGsCU9e-M8DQrnWze1kvuseGG7f29KxJqRkg"

# Usage: ./stitch_call.sh <json_file>
curl -s --connect-timeout 60 --max-time 120 -X POST "$API" \
  -H "X-Goog-Api-Key: $KEY" \
  -H "Content-Type: application/json" \
  -d @"$1" 2>&1
