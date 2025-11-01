#!/bin/bash

# ClaudeVoice Quick Start Script
# This script starts the voice agent with proper environment setup

echo "=================================="
echo "🎙️ Starting ClaudeVoice Agent"
echo "=================================="

# Navigate to agent directory
cd agent

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Run the agent
echo "Starting agent in development mode..."
echo ""
echo "Available commands:"
echo "  dev    - Development mode with LiveKit playground"
echo "  start  - Production mode"
echo "  --help - Show all options"
echo ""

# Run with the simplified version that's compatible with LiveKit 1.2.17
python main_simple.py ${1:-dev}