#!/bin/bash

# Script to fetch Claude Code hooks documentation from Anthropic docs
# and save it to docs/what-is-cc-hook.md

set -e

URL="https://docs.claude.com/en/docs/claude-code/hooks.md"
OUTPUT_DIR="docs"
OUTPUT_FILE="$OUTPUT_DIR/what-is-cc-hook.md"

echo "Fetching Claude Code hooks documentation..."

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Fetch the documentation using curl
curl -s "$URL" > "$OUTPUT_FILE"

echo "Documentation saved to $OUTPUT_FILE"
