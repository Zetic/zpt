# Discord Image Modification Bot

A Discord bot that uses Replicate API to modify images using AI. The bot responds to image replies with custom prompts to transform images using the flux-kontext-max model.

## Features

- Reply to images in Discord with AI-powered modifications
- Uses Replicate's flux-kontext-max model for image transformation
- Comprehensive logging and error handling
- Automatic image storage (input and output)
- Configurable file size limits and channel restrictions
- Built-in help and status commands

## Setup

### Prerequisites

- Python 3.8 or higher
- Discord Bot Token
- Replicate API Token

### Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd zpt
```

2. Set up environment variables:
```bash
cp .env.example .env
```

3. Edit `.env` file with your tokens:
```bash
DISCORD_BOT_TOKEN=your_discord_bot_token_here
REPLICATE_API_TOKEN=your_replicate_api_token_here
```

4. Run the startup script:
```bash
./start_bot.sh
```

Or manually:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python discord_bot.py
```

## Usage

1. In Discord, find a message with an image
2. Reply to that message
3. Mention the bot (@bot_name) in your reply
4. Include a description of how you want to modify the image

Example:
```
@ImageBot Make the letters 3D and floating in space on a city street
```

The bot will:
1. Download the original image
2. Process it using Replicate's AI model
3. Save both input and output images
4. Send the modified image back to Discord

## Configuration

Environment variables in `.env`:

- `DISCORD_BOT_TOKEN`: Your Discord bot token (required)
- `REPLICATE_API_TOKEN`: Your Replicate API token (required)
- `ALLOWED_CHANNEL_ID`: Restrict bot to specific channel (optional)
- `IMAGES_FOLDER`: Directory for storing images (default: ./images)
- `MAX_FILE_SIZE_MB`: Maximum file size in MB (default: 25)

## Commands

- `!help`: Show usage instructions
- `!status`: Display bot status and configuration

## File Structure

```
zpt/
├── discord_bot.py          # Main bot code
├── requirements.txt        # Python dependencies
├── start_bot.sh           # Startup script
├── .env.example           # Environment template
├── images/                # Image storage
│   ├── input/            # Original images
│   └── output/           # Modified images
└── bot.log               # Bot logs
```

## Getting API Tokens

### Discord Bot Token

1. Go to https://discord.com/developers/applications
2. Create a new application
3. Go to "Bot" section
4. Create a bot and copy the token
5. Enable necessary intents (Message Content Intent)
6. Invite bot to your server with appropriate permissions

### Replicate API Token

1. Go to https://replicate.com
2. Sign up/log in
3. Go to your account settings
4. Generate an API token
5. Copy the token (starts with `r8_`)

## Logging

The bot provides comprehensive logging:
- Console output for real-time monitoring
- `bot.log` file for persistent logs
- Debug information for troubleshooting
- Error tracking and handling

## Troubleshooting

### Common Issues

1. **Bot not responding**: Check bot permissions and Message Content Intent
2. **API errors**: Verify your Replicate API token and account credits
3. **Image download fails**: Check image URL accessibility and file size
4. **Permission errors**: Ensure bot has necessary Discord permissions

### Debug Mode

Enable debug logging by modifying the logging level in `discord_bot.py`:
```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## Security Notes

- Never commit your `.env` file with actual tokens
- Keep your API tokens secure and rotate them regularly
- Monitor your Replicate API usage and costs
- Restrict bot usage to specific channels if needed

## Dependencies

- `discord.py`: Discord API wrapper
- `replicate`: Replicate API client
- `python-dotenv`: Environment variable management
- `requests`: HTTP requests
- `Pillow`: Image processing utilities
- `aiohttp`: Async HTTP client
- `aiofiles`: Async file operations

## License

This project is open source. Please check the repository for license details.
