#!/usr/bin/env python3
"""
Discord Bot with AI Integration Scaffold
A modular Discord bot designed for future AI integration.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

import discord
from discord.ext import commands

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from utils.logging_setup import setup_logging

class AIDiscordBot(commands.Bot):
    """Custom Discord bot class with AI integration capabilities."""
    
    def __init__(self):
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        # Initialize bot with command prefix and intents
        super().__init__(
            command_prefix=Config.BOT_PREFIX,
            intents=intents,
            help_command=commands.DefaultHelpCommand(no_category='Commands')
        )
        
        self.logger = logging.getLogger(__name__)
    
    async def setup_hook(self):
        """Setup hook called when the bot is starting up."""
        self.logger.info("Bot is starting up...")
        
        # Load all command cogs
        await self.load_extensions()
        
        # Sync slash commands (for future use)
        try:
            synced = await self.tree.sync()
            self.logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            self.logger.error(f"Failed to sync slash commands: {e}")
    
    async def load_extensions(self):
        """Load all command extensions/cogs."""
        commands_dir = Path("commands")
        
        if not commands_dir.exists():
            self.logger.warning("Commands directory not found")
            return
        
        for file_path in commands_dir.glob("*.py"):
            if file_path.name.startswith("__"):
                continue
            
            extension_name = f"commands.{file_path.stem}"
            try:
                await self.load_extension(extension_name)
                self.logger.info(f"Loaded extension: {extension_name}")
            except Exception as e:
                self.logger.error(f"Failed to load extension {extension_name}: {e}")
    
    async def on_ready(self):
        """Event called when the bot is ready."""
        self.logger.info(f"Bot is ready! Logged in as {self.user}")
        self.logger.info(f"Bot ID: {self.user.id}")
        self.logger.info(f"Connected to {len(self.guilds)} guilds")
        self.logger.info(f"Serving {len(self.users)} users")
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{Config.BOT_PREFIX}help | AI Integration Ready"
        )
        await self.change_presence(activity=activity, status=discord.Status.online)
    
    async def on_command_error(self, ctx, error):
        """Global error handler for commands."""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors
        
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Missing Required Argument",
                description=f"You're missing a required argument: `{error.param.name}`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Log unexpected errors
        self.logger.error(f"Unexpected error in command {ctx.command}: {error}")
        
        embed = discord.Embed(
            title="❌ An Error Occurred",
            description="An unexpected error occurred while processing your command.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    
    async def on_message(self, message):
        """Event called when a message is sent."""
        # Ignore messages from bots
        if message.author.bot:
            return
        
        # Process commands
        await self.process_commands(message)

async def main():
    """Main function to run the bot."""
    # Setup logging
    logger = setup_logging()
    
    # Validate configuration
    if not Config.validate():
        logger.error("Configuration validation failed. Please check your .env file.")
        sys.exit(1)
    
    # Create and run the bot
    bot = AIDiscordBot()
    
    try:
        await bot.start(Config.DISCORD_TOKEN)
    except discord.LoginFailure:
        logger.error("Invalid Discord token. Please check your DISCORD_TOKEN in .env file.")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        await bot.close()

if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())