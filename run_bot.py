#!/usr/bin/env python3
"""
Simple startup script for the Discord Flux Bot
"""

import os
import sys

def check_environment():
    """Check if required environment variables are set"""
    required_vars = ['DISCORD_TOKEN', 'REPLICATE_API_TOKEN']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Please create a .env file based on .env.example")
        print("   and add your Discord and Replicate API tokens.")
        return False
    
    return True

def main():
    print("🤖 Starting Discord Flux Bot...")
    
    if not check_environment():
        sys.exit(1)
    
    try:
        from bot import main as bot_main
        bot_main()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()