import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Bot Configuration"""
    
    # Discord
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    OWNER_ID = int(os.getenv('OWNER_ID', 0))
    DEFAULT_PREFIX = os.getenv('DEFAULT_PREFIX', ',')
    
    # API Keys
    LAST_FM_API_KEY = os.getenv('LAST_FM_API_KEY')
    LAST_FM_SECRET = os.getenv('LAST_FM_SECRET')
    SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    IGDB_CLIENT_ID = os.getenv('IGDB_CLIENT_ID')
    IGDB_ACCESS_TOKEN = os.getenv('IGDB_ACCESS_TOKEN')
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot.db')
    
    # Colors
    PRIMARY_COLOR = 0x5865f2
    SUCCESS_COLOR = 0x57f287
    ERROR_COLOR = 0xed4245
    WARNING_COLOR = 0xfaa61a
    INFO_COLOR = 0x00b0f4
