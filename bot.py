import os
import io
import discord
import replicate
from discord.ext import commands
from dotenv import load_dotenv
import aiohttp
from datetime import datetime

# Load environment variables
load_dotenv()

class FluxBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True
        super().__init__(command_prefix='!', intents=intents)
        
        # Configure Replicate
        self.replicate_client = replicate.Client(api_token=os.getenv('REPLICATE_API_TOKEN'))
        
        # Create directory structure for local storage
        self.setup_directories()
    
    def setup_directories(self):
        """Create required directory structure for image storage"""
        os.makedirs('images/inputs', exist_ok=True)
        os.makedirs('images/outputs', exist_ok=True)
    
    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        print(f'Bot is in {len(self.guilds)} guilds')
    
    async def on_message(self, message):
        # Don't respond to bot's own messages
        if message.author == self.user:
            return
        
        # Check if bot is mentioned and message is a reply to another message
        if self.user.mentioned_in(message) and message.reference:
            await self.handle_image_modification(message)
        
        # Process commands
        await self.process_commands(message)
    
    async def handle_image_modification(self, message):
        """Handle image modification when bot is mentioned in a reply"""
        try:
            # Get the original message being replied to
            referenced_message = await message.channel.fetch_message(message.reference.message_id)
            
            # Check if the referenced message has attachments (images)
            if not referenced_message.attachments:
                await message.reply("❌ The message you're replying to doesn't contain any images.")
                return
            
            # Find all image attachments
            image_attachments = []
            for attachment in referenced_message.attachments:
                if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp']):
                    image_attachments.append(attachment)
            
            # Validate exactly one image as per requirements
            if len(image_attachments) == 0:
                await message.reply("❌ No valid image found in the referenced message.")
                return
            elif len(image_attachments) > 1:
                await message.reply("❌ Please reply to a message with exactly one image. Multiple images are not supported.")
                return
            
            # Use the single image attachment
            image_attachment = image_attachments[0]
            
            # Extract the modification prompt from the reply (excluding the bot mention)
            prompt = message.content
            # Remove bot mention from prompt
            for mention in message.mentions:
                if mention == self.user:
                    prompt = prompt.replace(f'<@{mention.id}>', '').strip()
            
            if not prompt:
                await message.reply("❌ Please provide a description of how you want to modify the image.")
                return
            
            # Send initial processing message
            processing_msg = await message.reply("🎨 Processing your image modification request...")
            
            # Save input image locally and use Discord URL directly
            input_filename = await self.save_input_image(image_attachment)
            
            # Use Flux Kontext for image modification with Discord URL
            await self.modify_image_with_flux(processing_msg, image_attachment.url, prompt, image_attachment.filename, input_filename)
            
        except Exception as e:
            print(f"Error in handle_image_modification: {e}")
            await message.reply(f"❌ An error occurred while processing your request: {str(e)}")
    
    async def save_input_image(self, attachment):
        """Save input image locally and return filename"""
        try:
            # Validate Discord URL format
            if not self.is_valid_discord_image_url(attachment.url):
                print(f"Warning: Invalid Discord image URL format: {attachment.url}")
                return None
            
            # Generate timestamp-based filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = os.path.splitext(attachment.filename)[1]
            input_filename = f"{timestamp}_input{file_extension}"
            input_path = os.path.join('images', 'inputs', input_filename)
            
            # Download and save the image
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status == 200:
                        image_data = await resp.read()
                        with open(input_path, 'wb') as f:
                            f.write(image_data)
                        print(f"Saved input image: {input_path}")
                        return input_filename
                    else:
                        print(f"Failed to download input image: {resp.status}")
                        return None
        except Exception as e:
            print(f"Error saving input image: {e}")
            return None
    
    def is_valid_discord_image_url(self, url):
        """Validate that the URL is a valid Discord image URL"""
        discord_domains = [
            'cdn.discordapp.com',
            'media.discordapp.net',
            'images-ext-1.discordapp.net',
            'images-ext-2.discordapp.net'
        ]
        
        valid_extensions = ['.png', '.jpg', '.jpeg', '.webp', '.gif']
        
        # Check if URL contains any Discord domain
        has_discord_domain = any(domain in url for domain in discord_domains)
        
        # Check if URL ends with valid image extension
        has_valid_extension = any(url.lower().endswith(ext) for ext in valid_extensions)
        
        return has_discord_domain and has_valid_extension
    
    async def modify_image_with_flux(self, processing_msg, image_url, prompt, original_filename, input_filename):
        """Use Flux Kontext to modify the image"""
        try:
            # Prepare the input for Flux Kontext using Discord URL directly
            input_data = {
                "image": image_url,  # Use Discord CDN URL directly
                "prompt": prompt,
                "num_inference_steps": 20,
                "guidance_scale": 3.5,
                "num_outputs": 1,
                "output_format": "png",
                "output_quality": 90
            }
            
            await processing_msg.edit(content="🎨 Generating modified image with Flux AI...")
            
            # Run the Flux Kontext model
            output = self.replicate_client.run(
                "black-forest-labs/flux-kontext-max",
                input=input_data
            )
            
            # Download and save the generated image
            if output:
                async with aiohttp.ClientSession() as session:
                    async with session.get(str(output)) as resp:
                        if resp.status == 200:
                            modified_image_data = await resp.read()
                            
                            # Save output image locally
                            output_filename = await self.save_output_image(modified_image_data, original_filename)
                            
                            # Create discord file and send
                            modified_filename = f"modified_{original_filename}"
                            discord_file = discord.File(
                                io.BytesIO(modified_image_data), 
                                filename=modified_filename
                            )
                            
                            await processing_msg.edit(
                                content=f"✅ Here's your modified image!\n**Prompt:** {prompt}\n**Input saved as:** {input_filename}\n**Output saved as:** {output_filename}",
                                attachments=[discord_file]
                            )
                        else:
                            await processing_msg.edit(content="❌ Failed to download the generated image.")
            else:
                await processing_msg.edit(content="❌ Failed to generate image. Please try again.")
                
        except Exception as e:
            print(f"Error in modify_image_with_flux: {e}")
            await processing_msg.edit(content=f"❌ Error generating image: {str(e)}")
    
    async def save_output_image(self, image_data, original_filename):
        """Save output image locally and return filename"""
        try:
            # Generate timestamp-based filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(original_filename)[0]
            output_filename = f"{timestamp}_output_{base_name}.png"
            output_path = os.path.join('images', 'outputs', output_filename)
            
            # Save the image
            with open(output_path, 'wb') as f:
                f.write(image_data)
            print(f"Saved output image: {output_path}")
            return output_filename
        except Exception as e:
            print(f"Error saving output image: {e}")
            return None

# Bot commands
@commands.command(name='help_flux')
async def help_flux(ctx):
    """Show help for Flux image modification"""
    help_text = """
**🎨 Flux Image Modification Bot**

**How to use:**
1. Find a message with **exactly one image** you want to modify
2. Reply to that message with your modification request
3. @mention me in your reply with a description

**Example:**
Reply to an image with: `@FluxBot make the sky more dramatic and stormy`

**Features:**
✅ Supports PNG, JPG, JPEG, WebP formats
✅ Uses Discord image URLs directly (faster processing)
✅ Saves input and output images locally for traceability
✅ Validates exactly one image per request
✅ Timestamp-based file naming

**Powered by:** Flux Kontext AI
    """
    await ctx.send(help_text)

def main():
    # Check for required environment variables
    discord_token = os.getenv('DISCORD_TOKEN')
    replicate_token = os.getenv('REPLICATE_API_TOKEN')
    
    if not discord_token:
        print("Error: DISCORD_TOKEN not found in environment variables.")
        print("Please create a .env file based on .env.example")
        return
    
    if not replicate_token:
        print("Error: REPLICATE_API_TOKEN not found in environment variables.")
        print("Please create a .env file based on .env.example")
        return
    
    # Create and run the bot
    bot = FluxBot()
    bot.add_command(help_flux)
    
    try:
        bot.run(discord_token)
    except Exception as e:
        print(f"Error running bot: {e}")

if __name__ == "__main__":
    main()