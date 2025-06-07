import discord
from discord.ext import commands
import logging

class BasicCommands(commands.Cog):
    """Basic commands for testing bot functionality."""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
    
    @commands.command(name='ping')
    async def ping(self, ctx):
        """Test command to check if the bot is responsive."""
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Bot latency: {latency}ms",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        self.logger.info(f"Ping command used by {ctx.author} in {ctx.guild}")
    
    @commands.command(name='hello')
    async def hello(self, ctx):
        """Friendly greeting command."""
        embed = discord.Embed(
            title="👋 Hello!",
            description=f"Hello, {ctx.author.mention}! I'm a Discord bot with AI integration capabilities.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Future Features",
            value="• AI chat integration\n• Image generation\n• Text summarization\n• And more!",
            inline=False
        )
        await ctx.send(embed=embed)
        self.logger.info(f"Hello command used by {ctx.author} in {ctx.guild}")
    
    @commands.command(name='status')
    async def status(self, ctx):
        """Display bot status and information."""
        embed = discord.Embed(
            title="🤖 Bot Status",
            color=discord.Color.orange()
        )
        embed.add_field(name="Status", value="Online ✅", inline=True)
        embed.add_field(name="Guilds", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="Users", value=len(self.bot.users), inline=True)
        embed.add_field(
            name="Commands",
            value=f"Prefix: `{self.bot.command_prefix}`\nType `{self.bot.command_prefix}help` for help",
            inline=False
        )
        await ctx.send(embed=embed)
        self.logger.info(f"Status command used by {ctx.author} in {ctx.guild}")

async def setup(bot):
    """Setup function to add this cog to the bot."""
    await bot.add_cog(BasicCommands(bot))