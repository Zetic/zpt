import os
import io
import discord
import replicate
from discord.ext import commands
from dotenv import load_dotenv
import aiohttp

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
            
            # Find the first image attachment
            image_attachment = None
            for attachment in referenced_message.attachments:
                if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp']):
                    image_attachment = attachment
                    break
            
            if not image_attachment:
                await message.reply("❌ No valid image found in the referenced message.")
                return
            
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
            
            # Download the image
            async with aiohttp.ClientSession() as session:
                async with session.get(image_attachment.url) as resp:
                    if resp.status == 200:
                        image_data = await resp.read()
                        image_file = io.BytesIO(image_data)
                    else:
                        await processing_msg.edit(content="❌ Failed to download the image.")
                        return
            
            # Use Flux Kontext for image modification
            await self.modify_image_with_flux(processing_msg, image_file, prompt, image_attachment.filename)
            
        except Exception as e:
            print(f"Error in handle_image_modification: {e}")
            await message.reply(f"❌ An error occurred while processing your request: {str(e)}")
    
    async def modify_image_with_flux(self, processing_msg, image_file, prompt, original_filename):
        """Use Flux Kontext to modify the image"""
        try:
            # Prepare the input for Flux Kontext
            input_data = {
                "image": image_file,
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
            
            # Download the generated image
            if output:
                async with aiohttp.ClientSession() as session:
                    async with session.get(str(output)) as resp:
                        if resp.status == 200:
                            modified_image_data = await resp.read()
                            
                            # Create discord file and send
                            modified_filename = f"modified_{original_filename}"
                            discord_file = discord.File(
                                io.BytesIO(modified_image_data), 
                                filename=modified_filename
                            )
                            
                            await processing_msg.edit(
                                content=f"✅ Here's your modified image!\n**Prompt:** {prompt}",
                                attachments=[discord_file]
                            )
                        else:
                            await processing_msg.edit(content="❌ Failed to download the generated image.")
            else:
                await processing_msg.edit(content="❌ Failed to generate image. Please try again.")
                
        except Exception as e:
            print(f"Error in modify_image_with_flux: {e}")
            await processing_msg.edit(content=f"❌ Error generating image: {str(e)}")

# Bot commands
@commands.command(name='help_flux')
async def help_flux(ctx):
    """Show help for Flux image modification"""
    help_text = """
**🎨 Flux Image Modification Bot**

**How to use:**
1. Find a message with an image you want to modify
2. Reply to that message with your modification request
3. @mention me in your reply with a description

**Example:**
Reply to an image with: `@FluxBot make the sky more dramatic and stormy`

**Supported formats:** PNG, JPG, JPEG, WebP
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