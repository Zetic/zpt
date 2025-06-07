# ZPT - Discord Bot with AI Integration

A modular Discord bot written in Python, designed for future AI integration including OpenAI APIs, image generation, and local LLM support.

## Features

- 🤖 **Discord Bot Foundation**: Built with discord.py for reliable Discord integration
- 🔧 **Modular Architecture**: Extensible command system using cogs
- 📝 **Logging System**: Comprehensive logging with file and console output
- 🌐 **Environment Configuration**: Secure environment variable management
- 🚀 **AI-Ready**: Structured for future AI tool integration
- 📦 **Plugin Support**: Easy to add new features without core rewrites

## Quick Start

### Prerequisites

- Python 3.8 or higher
- A Discord Application/Bot Token

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Zetic/zpt.git
   cd zpt
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your Discord bot token:
   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   ```

4. **Run the bot:**
   ```bash
   python bot.py
   ```

### Getting a Discord Bot Token

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" section
4. Click "Add Bot"
5. Copy the bot token and add it to your `.env` file
6. Invite the bot to your server using the OAuth2 URL generator

## Commands

The bot comes with basic commands to test functionality:

- `!ping` - Test bot responsiveness
- `!hello` - Friendly greeting with feature preview
- `!status` - Display bot status and information
- `!help` - Show all available commands

## Project Structure

```
zpt/
├── bot.py              # Main bot file
├── config.py           # Configuration management
├── requirements.txt    # Python dependencies
├── .env.example       # Environment variables template
├── .gitignore         # Git ignore file
├── commands/          # Modular command cogs
│   ├── __init__.py
│   └── basic.py       # Basic test commands
├── utils/             # Utility modules
│   ├── __init__.py
│   └── logging_setup.py
└── logs/              # Log files (created automatically)
```

## Configuration

The bot can be configured through environment variables in the `.env` file:

- `DISCORD_TOKEN`: Your Discord bot token (required)
- `BOT_PREFIX`: Command prefix (default: `!`)
- `BOT_STATUS`: Bot status (default: `online`)
- `LOG_LEVEL`: Logging level (default: `INFO`)

## Future AI Integration

The bot is structured to easily integrate AI capabilities:

- **OpenAI Integration**: Ready for GPT chat, completions, and embeddings
- **Image Generation**: Prepared for Stable Diffusion and DALL-E integration
- **Local LLM Support**: Architecture supports local language models
- **Plugin System**: Modular design for easy feature additions

## Development

### Adding New Commands

1. Create a new file in the `commands/` directory
2. Define your command cog class
3. Add an `async def setup(bot)` function
4. The bot will automatically load your commands on startup

Example command cog:
```python
from discord.ext import commands

class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def mycommand(self, ctx):
        await ctx.send("Hello from my command!")

async def setup(bot):
    await bot.add_cog(MyCog(bot))
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. Please check the license file for details.

## Support

For issues and questions, please use the GitHub issue tracker.
