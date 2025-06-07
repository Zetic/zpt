# Development and Deployment Guide

## Quick Start for Development

1. **Clone and setup**:
   ```bash
   git clone https://github.com/Zetic/zpt.git
   cd zpt
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your actual tokens
   ```

3. **Run the bot**:
   ```bash
   python run_bot.py
   ```

## Testing

Run validation tests:
```bash
python test_bot.py
```

## Bot Commands

### For Users
- Reply to any image with `@BotName your modification request`
- Use `!help_flux` for detailed help

### Examples
- `@FluxBot make the sky more dramatic`
- `@FluxBot add a sunset background`
- `@FluxBot convert this to black and white`

## API Requirements

### Discord Bot Setup
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create new application → Bot
3. Copy bot token to `.env`
4. Enable "Message Content Intent"
5. Invite bot to server with proper permissions

### Replicate API Setup
1. Sign up at [Replicate](https://replicate.com)
2. Generate API token
3. Add to `.env`

## Deployment Options

### Local Development
```bash
python run_bot.py
```

### Production (systemd service)
```ini
[Unit]
Description=Discord Flux Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/zpt
ExecStart=/usr/bin/python3 run_bot.py
Restart=always
RestartSec=5
Environment=PATH=/usr/bin:/usr/local/bin
EnvironmentFile=/path/to/zpt/.env

[Install]
WantedBy=multi-user.target
```

### Docker (optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "run_bot.py"]
```

## Troubleshooting

- **Bot doesn't respond**: Check Message Content Intent is enabled
- **API errors**: Verify tokens in `.env` file
- **Import errors**: Run `pip install -r requirements.txt`
- **Permission errors**: Ensure bot has read/send message permissions

## Architecture

```
bot.py              # Main bot logic
├── FluxBot         # Discord bot class
├── on_message      # Message event handler
├── handle_image_modification  # Core image processing
└── modify_image_with_flux    # Flux API integration

run_bot.py          # Startup script with environment checks
test_bot.py         # Validation tests
requirements.txt    # Python dependencies
.env.example        # Environment template
```