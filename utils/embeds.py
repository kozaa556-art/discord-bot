import discord
from config import Config
from datetime import datetime

class EmbedBuilder:
    """Reusable embed builder"""
    
    @staticmethod
    def create(title: str = None, description: str = None, color: int = None, **kwargs) -> discord.Embed:
        """Create a standard embed"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color or Config.PRIMARY_COLOR,
            timestamp=datetime.utcnow()
        )
        
        if 'fields' in kwargs:
            for name, value, inline in kwargs['fields']:
                embed.add_field(name=name, value=value, inline=inline)
        
        if 'author' in kwargs:
            embed.set_author(name=kwargs['author']['name'], icon_url=kwargs['author'].get('icon_url'))
        
        if 'footer' in kwargs:
            embed.set_footer(text=kwargs['footer'], icon_url=kwargs.get('footer_icon'))
        elif 'ctx' in kwargs:
            embed.set_footer(text=f"Requested by {kwargs['ctx'].author}", icon_url=kwargs['ctx'].author.avatar.url)
        
        if 'thumbnail' in kwargs:
            embed.set_thumbnail(url=kwargs['thumbnail'])
        
        if 'image' in kwargs:
            embed.set_image(url=kwargs['image'])
        
        return embed
    
    @staticmethod
    def success(title: str, description: str = None, **kwargs) -> discord.Embed:
        """Create a success embed"""
        return EmbedBuilder.create(title=title, description=description, color=Config.SUCCESS_COLOR, **kwargs)
    
    @staticmethod
    def error(title: str, description: str = None, **kwargs) -> discord.Embed:
        """Create an error embed"""
        return EmbedBuilder.create(title=title, description=description, color=Config.ERROR_COLOR, **kwargs)
    
    @staticmethod
    def warning(title: str, description: str = None, **kwargs) -> discord.Embed:
        """Create a warning embed"""
        return EmbedBuilder.create(title=title, description=description, color=Config.WARNING_COLOR, **kwargs)
    
    @staticmethod
    def info(title: str, description: str = None, **kwargs) -> discord.Embed:
        """Create an info embed"""
        return EmbedBuilder.create(title=title, description=description, color=Config.INFO_COLOR, **kwargs)
    
    @staticmethod
    def usage(ctx, command: str, description: str, usage: str, example: str, permissions: str = None) -> discord.Embed:
        """Create a usage/help embed"""
        embed = EmbedBuilder.create(
            title=f"Command Usage: {command}",
            description=description,
            color=Config.INFO_COLOR,
            ctx=ctx
        )
        embed.add_field(name="Usage", value=f"```\n{usage}```", inline=False)
        embed.add_field(name="Example", value=f"```\n{example}```", inline=False)
        if permissions:
            embed.add_field(name="Required Permissions", value=permissions, inline=False)
        return embed
    
    @staticmethod
    def field_embed(title: str, description: str, fields: list, color: int = None, **kwargs) -> discord.Embed:
        """Create embed with multiple fields"""
        embed = EmbedBuilder.create(title=title, description=description, color=color or Config.PRIMARY_COLOR, **kwargs)
        for field in fields:
            embed.add_field(name=field['name'], value=field['value'], inline=field.get('inline', False))
        return embed
