#!/usr/bin/env python3
"""
Discord Bot with Replicate API Integration for Image Modification

This bot listens for replies to images where the bot is mentioned,
downloads the image, processes it using Replicate's flux-kontext-max model,
and sends the modified image back to the Discord channel.
"""

import asyncio
import os
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import hashlib
import json

import discord
from discord.ext import commands
import replicate
import aiohttp
import aiofiles
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Bot configuration
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
REPLICATE_TOKEN = os.getenv('REPLICATE_API_TOKEN')
ALLOWED_CHANNEL_ID = os.getenv('ALLOWED_CHANNEL_ID')
IMAGES_FOLDER = os.getenv('IMAGES_FOLDER', './images')
MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '25'))

# Create image directories
Path(f"{IMAGES_FOLDER}/input").mkdir(parents=True, exist_ok=True)
Path(f"{IMAGES_FOLDER}/output").mkdir(parents=True, exist_ok=True)

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

class ImageModificationBot:
    """Handles image modification using Replicate API"""
    
    def __init__(self):
        self.replicate_client = None
        self.session = None
        
    async def setup(self):
        """Initialize the bot components"""
        logger.info("Setting up ImageModificationBot...")
        
        # Validate tokens
        if not DISCORD_TOKEN:
            logger.error("DISCORD_BOT_TOKEN not found in environment variables")
            raise ValueError("Discord bot token is required")
            
        if not REPLICATE_TOKEN:
            logger.error("REPLICATE_API_TOKEN not found in environment variables")
            raise ValueError("Replicate API token is required")
        
        # Set up Replicate client
        os.environ['REPLICATE_API_TOKEN'] = REPLICATE_TOKEN
        self.replicate_client = replicate
        
        # Create aiohttp session for downloading images
        self.session = aiohttp.ClientSession()
        
        logger.info("ImageModificationBot setup completed successfully")
    
    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
            logger.info("HTTP session closed")
    
    async def download_image(self, url: str, filename: str) -> Optional[str]:
        """Download image from URL and save to local storage"""
        try:
            logger.info(f"Starting download of image from URL: {url}")
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Failed to download image: HTTP {response.status}")
                    return None
                
                # Check file size
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > MAX_FILE_SIZE_MB * 1024 * 1024:
                    logger.error(f"Image too large: {content_length} bytes")
                    return None
                
                # Save image
                file_path = f"{IMAGES_FOLDER}/input/{filename}"
                async with aiofiles.open(file_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)
                
                logger.info(f"Successfully downloaded image to: {file_path}")
                return file_path
                
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            return None
    
    async def modify_image_with_replicate(self, image_path: str, prompt: str) -> Optional[str]:
        """Use Replicate API to modify the image"""
        try:
            logger.info(f"Starting image modification with prompt: '{prompt}'")
            logger.info(f"Using input image: {image_path}")
            
            # Prepare input for Replicate
            with open(image_path, 'rb') as image_file:
                input_data = {
                    "prompt": prompt,
                    "input_image": image_file,
                    "output_format": "jpg"
                }
                
                logger.info("Sending request to Replicate API...")
                logger.debug(f"Input data: {json.dumps({k: v if k != 'input_image' else '<image_file>' for k, v in input_data.items()})}")
                
                # Call Replicate API
                output = self.replicate_client.run(
                    "black-forest-labs/flux-kontext-max",
                    input=input_data
                )
                
                logger.info("Received response from Replicate API")
                
                # Generate output filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                hash_suffix = hashlib.md5(prompt.encode()).hexdigest()[:8]
                output_filename = f"modified_{timestamp}_{hash_suffix}.jpg"
                output_path = f"{IMAGES_FOLDER}/output/{output_filename}"
                
                # Save output image
                logger.info(f"Saving modified image to: {output_path}")
                with open(output_path, "wb") as output_file:
                    output_file.write(output.read())
                
                logger.info("Image modification completed successfully")
                return output_path
                
        except Exception as e:
            logger.error(f"Error during image modification: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            return None
    
    def generate_filename(self, original_url: str, extension: str = "jpg") -> str:
        """Generate a unique filename for the image"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        url_hash = hashlib.md5(original_url.encode()).hexdigest()[:8]
        return f"input_{timestamp}_{url_hash}.{extension}"

# Create bot instance
image_bot = ImageModificationBot()

@bot.event
async def on_ready():
    """Called when the bot is ready"""
    logger.info(f"Bot logged in as {bot.user} (ID: {bot.user.id})")
    logger.info(f"Bot is ready and connected to {len(bot.guilds)} guilds")
    
    # Setup the image bot
    await image_bot.setup()
    
    # Log configuration
    logger.info(f"Images folder: {IMAGES_FOLDER}")
    logger.info(f"Max file size: {MAX_FILE_SIZE_MB}MB")
    if ALLOWED_CHANNEL_ID:
        logger.info(f"Restricted to channel ID: {ALLOWED_CHANNEL_ID}")
    else:
        logger.info("Bot will work in all channels")

@bot.event
async def on_message(message):
    """Handle incoming messages"""
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Log all messages for debugging
    logger.debug(f"Message from {message.author}: {message.content}")
    
    # Check if this is a reply to a message
    if not message.reference:
        logger.debug("Message is not a reply, ignoring")
        return
    
    # Check if bot is mentioned in the message
    if bot.user not in message.mentions:
        logger.debug("Bot not mentioned in message, ignoring")
        return
    
    # Check channel restrictions
    if ALLOWED_CHANNEL_ID and str(message.channel.id) != ALLOWED_CHANNEL_ID:
        logger.info(f"Message from restricted channel {message.channel.id}, ignoring")
        return
    
    logger.info(f"Processing message from {message.author} in channel {message.channel.name}")
    
    try:
        # Get the replied-to message
        replied_message = await message.channel.fetch_message(message.reference.message_id)
        logger.info(f"Found replied message from {replied_message.author}")
        
        # Check if the replied message has attachments (images)
        image_attachments = [att for att in replied_message.attachments 
                           if att.content_type and att.content_type.startswith('image/')]
        
        if not image_attachments:
            logger.info("No image attachments found in replied message")
            await message.reply("I need an image to modify. Please reply to a message that contains an image.")
            return
        
        # Get the first image attachment
        image_attachment = image_attachments[0]
        logger.info(f"Found image attachment: {image_attachment.filename} ({image_attachment.size} bytes)")
        
        # Extract the prompt from the message (remove bot mention)
        prompt = message.content
        for mention in message.mentions:
            prompt = prompt.replace(f"<@{mention.id}>", "").replace(f"<@!{mention.id}>", "")
        prompt = prompt.strip()
        
        if not prompt:
            logger.info("No prompt provided in message")
            await message.reply("Please provide a description of how you want to modify the image.")
            return
        
        logger.info(f"Using prompt: '{prompt}'")
        
        # Send initial response
        processing_message = await message.reply("Processing your image modification request...")
        
        # Download the image
        filename = image_bot.generate_filename(image_attachment.url, 
                                             image_attachment.filename.split('.')[-1])
        logger.info(f"Downloading image as: {filename}")
        
        image_path = await image_bot.download_image(image_attachment.url, filename)
        if not image_path:
            logger.error("Failed to download image")
            await processing_message.edit(content="Failed to download the image. Please try again.")
            return
        
        # Modify the image using Replicate
        logger.info("Starting image modification...")
        modified_image_path = await image_bot.modify_image_with_replicate(image_path, prompt)
        
        if not modified_image_path:
            logger.error("Failed to modify image")
            await processing_message.edit(content="Failed to modify the image. Please try again later.")
            return
        
        # Send the modified image back
        logger.info(f"Sending modified image: {modified_image_path}")
        
        with open(modified_image_path, 'rb') as modified_file:
            file = discord.File(modified_file, filename=f"modified_{image_attachment.filename}")
            await processing_message.edit(
                content=f"Here's your modified image with prompt: '{prompt}'",
                attachments=[file]
            )
        
        logger.info("Image modification request completed successfully")
        
    except discord.NotFound:
        logger.error("Could not find the replied message")
        await message.reply("Could not find the message you replied to.")
    except discord.Forbidden:
        logger.error("Bot lacks permissions to access the message")
        await message.reply("I don't have permission to access that message.")
    except Exception as e:
        logger.error(f"Unexpected error processing message: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        await message.reply("An unexpected error occurred. Please try again later.")

@bot.event
async def on_error(event, *args, **kwargs):
    """Handle bot errors"""
    logger.error(f"An error occurred in event {event}: {args}")

@bot.command(name='help')
async def help_command(ctx):
    """Show help information"""
    help_text = """
**Image Modification Bot Help**

To use this bot:
1. Find a message with an image
2. Reply to that message
3. Mention me (@{bot_name}) in your reply
4. Include a description of how you want to modify the image

Example:
`@{bot_name} Make the letters 3D and floating in space`

The bot will download the image, process it using AI, and send back the modified version.

Both input and output images are saved for storage.
    """.format(bot_name=bot.user.name if bot.user else "Bot")
    
    await ctx.send(help_text)

@bot.command(name='status')
async def status_command(ctx):
    """Show bot status"""
    status_text = f"""
**Bot Status**
- Connected: Yes
- Guilds: {len(bot.guilds)}
- Latency: {round(bot.latency * 1000)}ms
- Images folder: {IMAGES_FOLDER}
- Max file size: {MAX_FILE_SIZE_MB}MB
    """
    
    await ctx.send(status_text)

async def main():
    """Main function to run the bot"""
    try:
        logger.info("Starting Discord bot...")
        await bot.start(DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
    finally:
        await image_bot.cleanup()
        await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)