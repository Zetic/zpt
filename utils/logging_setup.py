import logging
import os
from datetime import datetime
import coloredlogs
from config import Config

def setup_logging():
    """Setup logging configuration for the bot."""
    
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"bot_{timestamp}.log")
    
    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Set up file logging
    logging.basicConfig(
        level=Config.get_log_level(),
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # Also log to console
        ]
    )
    
    # Set up colored console logging
    coloredlogs.install(
        level=Config.get_log_level(),
        fmt=log_format,
        logger=logging.getLogger()
    )
    
    # Reduce discord.py logging noise
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('discord.http').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_file}")
    logger.info(f"Log level: {Config.LOG_LEVEL}")
    
    return logger