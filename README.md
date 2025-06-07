# ZPT - Discord Flux AI Bot

A Discord bot that uses Flux AI to modify images based on text prompts. Users can reply to images in Discord and mention the bot to generate modified versions using Flux Kontext.

## Features

- 🎨 Image modification using Flux Kontext AI
- 💬 Reply-based interaction system
- 🖼️ Support for PNG, JPG, JPEG, and WebP formats
- ⚡ Asynchronous processing for better performance

## Setup

### Prerequisites

- Python 3.8+
- Discord Bot Token
- Replicate API Token

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Zetic/zpt.git
cd zpt
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create environment file:
```bash
cp .env.example .env
```

4. Edit `.env` file with your tokens:
```
DISCORD_TOKEN=your_discord_bot_token_here
REPLICATE_API_TOKEN=your_replicate_api_token_here
```

### Getting API Keys

#### Discord Bot Token
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "Bot" section
4. Create a bot and copy the token
5. Enable "Message Content Intent" in Bot settings

#### Replicate API Token
1. Sign up at [Replicate](https://replicate.com)
2. Go to your [API tokens page](https://replicate.com/account/api-tokens)
3. Create a new token and copy it

## Usage

### Running the Bot

```bash
python bot.py
```

### Using the Bot in Discord

1. **Find an image** you want to modify in any Discord channel
2. **Reply to that message** with your modification request
3. **@mention the bot** in your reply with a description

**Example:**
```
@FluxBot make the sky more dramatic and stormy
```

The bot will:
- Download the original image
- Process it with Flux Kontext AI using your prompt
- Reply with the modified image

### Commands

- `!help_flux` - Show detailed help information

## Technical Details

### Dependencies

- `discord.py` - Discord API wrapper
- `replicate` - Replicate API client for Flux AI
- `python-dotenv` - Environment variable management
- `aiohttp` - Async HTTP client for image downloads

### Flux Kontext Integration

The bot uses the [Flux Kontext Max](https://replicate.com/black-forest-labs/flux-kontext-max) model for image modifications. This model specializes in understanding and modifying images based on text prompts while maintaining the original image's context.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is open source and available under the MIT License.
