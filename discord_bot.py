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
from typing import Optional, Dict, Any, List
import hashlib
import json
import io

import discord
from discord.ext import commands
import replicate
import aiohttp
import aiofiles
from dotenv import load_dotenv
from PIL import Image

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

class OutputImage:
    """Represents an output image with metadata"""
    def __init__(self, image_path: str, prompt: str, filename: str):
        self.image_path = image_path
        self.prompt = prompt
        self.filename = filename
        self.image = None
        
    def load_image(self):
        """Load the PIL Image object"""
        if self.image is None and os.path.exists(self.image_path):
            self.image = Image.open(self.image_path)
        return self.image

class ImageProcessingView(discord.ui.View):
    """Interactive view for image processing with timeout handling"""
    
    def __init__(self, *, timeout=1800):  # 30 minutes timeout
        super().__init__(timeout=timeout)
        self.outputs: List[OutputImage] = []
        self.message: Optional[discord.Message] = None
        self.processing = False
        
    async def on_timeout(self):
        """Handle view timeout - display all output images"""
        # Disable all interactive components
        for item in self.children:
            item.disabled = True
            
        if not self.message:
            return
            
        files = []
        embeds = []
        
        try:
            if not self.outputs:
                # No outputs generated
                embed = discord.Embed(
                    title="🕒 Session Timed Out",
                    description="No output images were generated during this session.",
                    color=discord.Color.orange()
                )
                embeds.append(embed)
            else:
                # Create embeds and files for all outputs
                for i, output in enumerate(self.outputs[:10]):  # Discord limit of 10 embeds
                    try:
                        # Load and prepare image
                        img = output.load_image()
                        if img:
                            img_buffer = io.BytesIO()
                            img.save(img_buffer, format='PNG')
                            img_buffer.seek(0)
                            
                            file = discord.File(img_buffer, filename=output.filename)
                            files.append(file)
                            
                            embed = discord.Embed(
                                title=f"Final Output {i+1}/{len(self.outputs)} (Timed Out)",
                                description=f"Prompt: {output.prompt[:100]}{'...' if len(output.prompt) > 100 else ''}",
                                color=discord.Color.orange()
                            )
                            embed.set_image(url=f"attachment://{output.filename}")
                            embeds.append(embed)
                    except Exception as e:
                        logger.error(f"Error preparing output {i}: {e}")
                        
                # Add info about additional outputs if more than 10
                if len(self.outputs) > 10:
                    info_embed = discord.Embed(
                        title="Additional Outputs",
                        description=f"Note: {len(self.outputs) - 10} additional output images were generated but cannot be displayed due to Discord's 10-embed limit.",
                        color=discord.Color.blue()
                    )
                    embeds.insert(0, info_embed)
                    
            # Update the message
            await self.message.edit(
                content="🕒 **Timed out!** Here are all your output images:",
                embeds=embeds,
                attachments=files,
                view=None
            )
            
        except Exception as e:
            logger.error(f"Error in timeout handler: {e}")
            try:
                await self.message.edit(
                    content="🕒 Session timed out. An error occurred while displaying output images.",
                    view=None
                )
            except:
                pass
                
    def add_output(self, output_image: OutputImage):
        """Add an output image to the session"""
        self.outputs.append(output_image)
        
    @discord.ui.button(label='Process Image', style=discord.ButtonStyle.primary, emoji='🎨')
    async def process_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle image processing button click"""
        if self.processing:
            await interaction.response.send_message("Already processing an image. Please wait...", ephemeral=True)
            return
            
        await interaction.response.send_message("Image processing feature would be implemented here.", ephemeral=True)
        
    @discord.ui.button(label='View Outputs', style=discord.ButtonStyle.secondary, emoji='📂')
    async def view_outputs_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle view outputs button click"""
        if not self.outputs:
            await interaction.response.send_message("No output images generated yet.", ephemeral=True)
            return
            
        # Show current outputs (simplified for now)
        embed = discord.Embed(
            title="Current Outputs",
            description=f"Generated {len(self.outputs)} output image(s) so far.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

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
        
        # Create an OutputImage object
        output_filename = f"modified_{image_attachment.filename}"
        output_image = OutputImage(modified_image_path, prompt, output_filename)
        
        # Check if we should use interactive mode (for demonstration of timeout feature)
        # For now, we'll use the simple mode but include the infrastructure
        use_interactive = message.content.lower().find('interactive') != -1
        
        if use_interactive:
            # Create and send an interactive view
            view = ImageProcessingView()
            view.add_output(output_image)
            
            # Create embed for the output
            embed = discord.Embed(
                title="Image Processing Complete",
                description=f"Generated image with prompt: '{prompt}'",
                color=discord.Color.green()
            )
            
            with open(modified_image_path, 'rb') as modified_file:
                file = discord.File(modified_file, filename=output_filename)
                embed.set_image(url=f"attachment://{output_filename}")
                
                view_message = await processing_message.edit(
                    content="✅ **Image processed!** Use the buttons below to interact:",
                    embed=embed,
                    attachments=[file],
                    view=view
                )
                view.message = view_message
        else:
            # Use the original simple mode
            with open(modified_image_path, 'rb') as modified_file:
                file = discord.File(modified_file, filename=output_filename)
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

@bot.command(name='bothelp')
async def help_command(ctx):
    """Show help information"""
    help_text = """
**Image Modification Bot Help**

**Basic Usage:**
1. Find a message with an image
2. Reply to that message
3. Mention me (@{bot_name}) in your reply
4. Include a description of how you want to modify the image

Example:
`@{bot_name} Make the letters 3D and floating in space`

**Interactive Mode:**
Add the word "interactive" to your prompt to use the new interactive mode with timeout handling:
`@{bot_name} interactive Make this image look futuristic`

**Test Commands:**
• `!test_timeout` - Test the timeout functionality with sample outputs
• `!status` - Show bot status and configuration

The bot will download the image, process it using AI, and send back the modified version.
Both input and output images are saved for storage.

**Interactive Sessions:**
- Interactive sessions timeout after 30 minutes
- When a session times out, all generated output images are automatically displayed
- Use the buttons to interact with ongoing sessions
    """.format(bot_name=bot.user.name if bot.user else "Bot")
    
    await ctx.send(help_text)

@bot.command(name='test_timeout')
async def test_timeout_command(ctx):
    """Test the timeout functionality with sample outputs"""
    logger.info(f"Testing timeout functionality for user {ctx.author}")
    
    # Create a view with a short timeout for testing (30 seconds)
    view = ImageProcessingView(timeout=30.0)
    
    # Create some sample output images for demonstration
    try:
        # Create a sample image in memory
        sample_img = Image.new('RGB', (100, 100), color='red')
        
        # Save to temporary location
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sample_path = f"{IMAGES_FOLDER}/output/sample_{timestamp}.png"
        sample_img.save(sample_path)
        
        # Create OutputImage objects
        output1 = OutputImage(sample_path, "Sample prompt 1", f"sample1_{timestamp}.png")
        output2 = OutputImage(sample_path, "Sample prompt 2 with a much longer description that will be truncated", f"sample2_{timestamp}.png")
        
        view.add_output(output1)
        view.add_output(output2)
        
        # Create initial embed
        embed = discord.Embed(
            title="🧪 Timeout Test Session",
            description="This interactive session will timeout in 30 seconds.\nAfter timeout, all output images will be displayed automatically.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Instructions", 
            value="Wait 30 seconds to see the timeout behavior, or use the buttons to interact.",
            inline=False
        )
        
        # Send with the view
        message = await ctx.send(embed=embed, view=view)
        view.message = message
        
        logger.info("Test timeout session created successfully")
        
    except Exception as e:
        logger.error(f"Error creating test timeout session: {e}")
        await ctx.send("Error creating test session. Please check the logs.")

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