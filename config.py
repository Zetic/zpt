import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration management for the Discord bot."""
    
    # Discord Configuration
    DISCORD_TOKEN: str = os.getenv('DISCORD_TOKEN', '')
    BOT_PREFIX: str = os.getenv('BOT_PREFIX', '!')
    BOT_STATUS: str = os.getenv('BOT_STATUS', 'online')
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # Future AI Integration
    OPENAI_API_KEY: Optional[str] = os.getenv('OPENAI_API_KEY')
    STABILITY_API_KEY: Optional[str] = os.getenv('STABILITY_API_KEY')
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present."""
        if not cls.DISCORD_TOKEN:
            logging.error("DISCORD_TOKEN is required but not set in environment variables")
            return False
        return True
    
    @classmethod
    def get_log_level(cls) -> int:
        """Convert string log level to logging constant."""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        return level_map.get(cls.LOG_LEVEL.upper(), logging.INFO)