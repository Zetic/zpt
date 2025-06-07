#!/bin/bash

# Discord Bot Startup Script
# This script sets up the environment and starts the Discord bot

echo "Starting Discord Image Modification Bot..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check for environment file
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found!"
    echo "Please copy .env.example to .env and fill in your tokens:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    echo ""
    echo "Required environment variables:"
    echo "  - DISCORD_BOT_TOKEN: Your Discord bot token"
    echo "  - REPLICATE_API_TOKEN: Your Replicate API token"
    exit 1
fi

# Start the bot
echo "Starting bot..."
python discord_bot.py