import discord
from discord.ext import commands
import asyncio
import aiohttp
from datetime import timedelta
import re
import sqlite3
from contextlib import asynccontextmanager

class DatabaseManager:
    """Handle database operations"""
    
    def __init__(self, db_path: str = 'bot.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Guild settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                prefix TEXT DEFAULT ',',
                modlog_channel INTEGER,
                joinlog_channel INTEGER,
                muted_role INTEGER,
                jail_channel INTEGER,
                jail_role INTEGER,
                base_role INTEGER,
                staff_role INTEGER,
                dj_role INTEGER,
                premium_role INTEGER,
                immute_role INTEGER,
                reactmute_role INTEGER,
                auto_nick TEXT,
                google_safety INTEGER DEFAULT 1,
                disable_custom_fms INTEGER DEFAULT 0,
                jail_roles INTEGER DEFAULT 0,
                autoplay TEXT DEFAULT 'off'
            )
        ''')
        
        # User data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                guild_id INTEGER,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 0,
                warnings INTEGER DEFAULT 0,
                UNIQUE(user_id, guild_id)
            )
        ''')
        
        # Cases
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cases (
                case_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                moderator_id INTEGER,
                action TEXT,
                reason TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                duration TEXT,
                resolved INTEGER DEFAULT 0
            )
        ''')
        
        # Aliases
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS aliases (
                guild_id INTEGER,
                alias TEXT,
                command TEXT,
                PRIMARY KEY(guild_id, alias)
            )
        ''')
        
        # Welcome/Goodbye
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                guild_id INTEGER,
                message_type TEXT,
                channel_id INTEGER,
                content TEXT,
                PRIMARY KEY(guild_id, message_type, channel_id)
            )
        ''')
        
        # Autoresponder
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS autoresponder (
                guild_id INTEGER,
                trigger TEXT,
                response TEXT,
                PRIMARY KEY(guild_id, trigger)
            )
        ''')
        
        # Filter settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS filter_settings (
                guild_id INTEGER,
                filter_type TEXT,
                channel_id INTEGER,
                enabled INTEGER,
                value TEXT,
                PRIMARY KEY(guild_id, filter_type, channel_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    @asynccontextmanager
    async def get_db(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

class HTTPClient:
    """Handle HTTP requests"""
    
    @staticmethod
    async def get(url: str, **kwargs):
        """Make GET request"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url, **kwargs) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
    
    @staticmethod
    async def post(url: str, **kwargs):
        """Make POST request"""
        async with aiohttp.ClientSession() as session:
            async with session.post(url, **kwargs) as resp:
                if resp.status in [200, 201]:
                    return await resp.json()
                return None

class TimeParser:
    """Parse time strings"""
    
    @staticmethod
    def parse_duration(duration_str: str) -> timedelta:
        """Parse duration string like '1h', '30m', '7d'"""
        units = {
            's': 'seconds',
            'm': 'minutes',
            'h': 'hours',
            'd': 'days',
            'w': 'weeks'
        }
        
        pattern = r'(\d+)([smhdw])'
        matches = re.findall(pattern, duration_str.lower())
        
        if not matches:
            return None
        
        kwargs = {}
        for value, unit in matches:
            kwargs[units[unit]] = int(value)
        
        return timedelta(**kwargs)
    
    @staticmethod
    def format_duration(td: timedelta) -> str:
        """Format timedelta to readable string"""
        total_seconds = int(td.total_seconds())
        
        weeks = total_seconds // 604800
        days = (total_seconds % 604800) // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        parts = []
        if weeks: parts.append(f"{weeks}w")
        if days: parts.append(f"{days}d")
        if hours: parts.append(f"{hours}h")
        if minutes: parts.append(f"{minutes}m")
        if seconds: parts.append(f"{seconds}s")
        
        return ' '.join(parts)

class PermissionChecker:
    """Check member permissions"""
    
    @staticmethod
    async def check_permissions(member: discord.Member, *permissions: str) -> bool:
        """Check if member has permissions"""
        perms = member.guild.get_member(member.id).guild_permissions
        return all(getattr(perms, perm, False) for perm in permissions)
    
    @staticmethod
    async def has_role(member: discord.Member, role: discord.Role) -> bool:
        """Check if member has role"""
        return role in member.roles

class MemberUtils:
    """Member utility functions"""
    
    @staticmethod
    async def get_member(guild: discord.Guild, identifier: str) -> discord.Member:
        """Get member by ID, mention, or name"""
        try:
            member_id = int(identifier.replace('<@', '').replace('>', ''))
            return guild.get_member(member_id)
        except:
            return discord.utils.find(lambda m: m.name.lower() == identifier.lower(), guild.members)
    
    @staticmethod
    async def safe_send(user: discord.User, embed: discord.Embed) -> bool:
        """Safely send DM to user"""
        try:
            await user.send(embed=embed)
            return True
        except:
            return False

class ColorUtils:
    """Color utility functions"""
    
    @staticmethod
    def hex_to_int(hex_color: str) -> int:
        """Convert hex color to int"""
        hex_color = hex_color.lstrip('#')
        return int(hex_color, 16)
    
    @staticmethod
    def int_to_hex(color_int: int) -> str:
        """Convert int color to hex"""
        return f"#{color_int:06x}"
    
    @staticmethod
    def is_valid_hex(hex_color: str) -> bool:
        """Check if hex color is valid"""
        return bool(re.match(r'^#?[0-9a-f]{6}$', hex_color, re.I))

db = DatabaseManager()
