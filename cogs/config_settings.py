import discord
from discord.ext import commands
from utils.embeds import EmbedBuilder
from utils.helpers import db, PermissionChecker, ColorUtils
import sqlite3

class ConfigSettings(commands.Cog):
    """Guild Configuration Settings"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def cog_check(self, ctx):
        """Check if user has admin permissions"""
        return ctx.author.guild_permissions.administrator
    
    def get_guild_setting(self, guild_id: int, setting: str):
        """Get guild setting from database"""
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute(f'SELECT {setting} FROM guild_settings WHERE guild_id = ?', (guild_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def set_guild_setting(self, guild_id: int, setting: str, value):
        """Set guild setting in database"""
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute(f'INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)', (guild_id,))
        cursor.execute(f'UPDATE guild_settings SET {setting} = ? WHERE guild_id = ?', (value, guild_id))
        conn.commit()
        conn.close()
    
    @commands.group(invoke_without_command=True)
    async def prefix(self, ctx):
        """View or manage server prefix"""
        prefix = self.get_guild_setting(ctx.guild.id, 'prefix') or ','
        embed = EmbedBuilder.info(
            title="Current Prefix",
            description=f"Server prefix: `{prefix}`",
            ctx=ctx
        )
        embed.add_field(name="Usage", value="`,prefix self <new_prefix>` - Set personal prefix\n`,prefix set <new_prefix>` - Set server prefix\n`,prefix remove` - Reset to default", inline=False)
        await ctx.send(embed=embed)
    
    @prefix.command(name='self')
    async def prefix_self(self, ctx, new_prefix: str):
        """Set personal prefix"""
        self.set_guild_setting(ctx.author.id, 'prefix', new_prefix)
        embed = EmbedBuilder.success(
            title="Prefix Updated",
            description=f"Your personal prefix is now `{new_prefix}`",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @prefix.command(name='set')
    async def prefix_set(self, ctx, new_prefix: str):
        """Set server prefix"""
        if len(new_prefix) > 5:
            embed = EmbedBuilder.error(
                title="Invalid Prefix",
                description="Prefix must be 5 characters or less",
                ctx=ctx
            )
            return await ctx.send(embed=embed)
        
        self.set_guild_setting(ctx.guild.id, 'prefix', new_prefix)
        embed = EmbedBuilder.success(
            title="Server Prefix Updated",
            description=f"New prefix: `{new_prefix}`",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @prefix.command(name='remove')
    async def prefix_remove(self, ctx):
        """Reset prefix to default"""
        self.set_guild_setting(ctx.guild.id, 'prefix', ',')
        embed = EmbedBuilder.success(
            title="Prefix Reset",
            description="Server prefix reset to `,`",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @commands.group(invoke_without_command=True)
    async def boosterrole(self, ctx):
        """Manage booster role features"""
        embed = EmbedBuilder.info(
            title="Booster Role",
            description="Manage special roles for server boosters",
            ctx=ctx
        )
        embed.add_field(
            name="Commands",
            value="`,boosterrole share` - Share role with member\n`,boosterrole color` - Change role color\n`,boosterrole list` - List all booster roles",
            inline=False
        )
        await ctx.send(embed=embed)
    
    @boosterrole.command(name='share')
    async def boosterrole_share(self, ctx, member: discord.Member = None):
        """Share booster role with member"""
        if not member:
            embed = EmbedBuilder.usage(
                ctx,
                "boosterrole share",
                "Share your booster role with another member",
                ",boosterrole share <@member>",
                ",boosterrole share @user",
                "Booster role owner"
            )
            return await ctx.send(embed=embed)
        
        embed = EmbedBuilder.success(
            title="Role Shared",
            description=f"Role shared with {member.mention}",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @boosterrole.command(name='color')
    async def boosterrole_color(self, ctx, color: str, second_color: str = None, *, name: str = None):
        """Change booster role color"""
        if not ColorUtils.is_valid_hex(color):
            embed = EmbedBuilder.error(
                title="Invalid Color",
                description="Please provide a valid hex color code (e.g., #ff0000)",
                ctx=ctx
            )
            return await ctx.send(embed=embed)
        
        embed = EmbedBuilder.success(
            title="Color Updated",
            description=f"Booster role color changed to {color}",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @boosterrole.command(name='list')
    async def boosterrole_list(self, ctx):
        """List all booster roles"""
        embed = EmbedBuilder.info(
            title="Booster Roles",
            description="All booster roles in this server",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @boosterrole.command(name='remove')
    async def boosterrole_remove(self, ctx):
        """Remove booster role system"""
        embed = EmbedBuilder.success(
            title="Booster Role System Removed",
            description="All booster roles have been disabled",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @boosterrole.command(name='link')
    async def boosterrole_link(self, ctx, member: discord.Member, role: discord.Role):
        """Link member to booster role"""
        embed = EmbedBuilder.success(
            title="Role Linked",
            description=f"Linked {member.mention} to {role.mention}",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @boosterrole.command(name='limit')
    async def boosterrole_limit(self, ctx, limit: int):
        """Set booster role limit"""
        self.set_guild_setting(ctx.guild.id, 'booster_limit', limit)
        embed = EmbedBuilder.success(
            title="Limit Set",
            description=f"Booster role limit set to {limit}",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @boosterrole.command(name='icon')
    async def boosterrole_icon(self, ctx, url: str):
        """Set booster role icon"""
        embed = EmbedBuilder.success(
            title="Icon Updated",
            description="Booster role icon has been updated",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @boosterrole.command(name='award')
    async def boosterrole_award(self, ctx, role: discord.Role = None):
        """Award booster role"""
        if not role:
            embed = EmbedBuilder.usage(
                ctx,
                "boosterrole award",
                "Award a role to server boosters",
                ",boosterrole award <@role>",
                ",boosterrole award @Members",
                "Administrator"
            )
            return await ctx.send(embed=embed)
        
        embed = EmbedBuilder.success(
            title="Role Awarded",
            description=f"{role.mention} has been awarded to boosters",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @boosterrole.command(name='rename')
    async def boosterrole_rename(self, ctx, *, name: str):
        """Rename booster role"""
        embed = EmbedBuilder.success(
            title="Role Renamed",
            description=f"Booster role renamed to {name}",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @commands.group(invoke_without_command=True)
    async def settings(self, ctx):
        """View or manage guild settings"""
        embed = EmbedBuilder.info(
            title="Guild Settings",
            description="Configure your server",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @settings.command(name='baserole')
    async def settings_baserole(self, ctx, role: discord.Role = None):
        """Set base role for new members"""
        if not role:
            embed = EmbedBuilder.usage(
                ctx,
                "settings baserole",
                "Set the role given to all new members",
                ",settings baserole <@role>",
                ",settings baserole @Members",
                "Administrator"
            )
            return await ctx.send(embed=embed)
        
        self.set_guild_setting(ctx.guild.id, 'base_role', role.id)
        embed = EmbedBuilder.success(
            title="Base Role Set",
            description=f"Base role is now {role.mention}",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @settings.command(name='modlog')
    async def settings_modlog(self, ctx, channel: discord.TextChannel = None):
        """Set moderation log channel"""
        if not channel:
            embed = EmbedBuilder.usage(
                ctx,
                "settings modlog",
                "Set the channel for moderation logs",
                ",settings modlog <#channel>",
                ",settings modlog #mod-logs",
                "Administrator"
            )
            return await ctx.send(embed=embed)
        
        self.set_guild_setting(ctx.guild.id, 'modlog_channel', channel.id)
        embed = EmbedBuilder.success(
            title="Modlog Channel Set",
            description=f"Modlog channel is now {channel.mention}",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @settings.command(name='muted')
    async def settings_muted(self, ctx, role: discord.Role = None):
        """Set muted role"""
        if not role:
            embed = EmbedBuilder.usage(
                ctx,
                "settings muted",
                "Set the role for muted members",
                ",settings muted <@role>",
                ",settings muted @Muted",
                "Administrator"
            )
            return await ctx.send(embed=embed)
        
        self.set_guild_setting(ctx.guild.id, 'muted_role', role.id)
        embed = EmbedBuilder.success(
            title="Muted Role Set",
            description=f"Muted role is now {role.mention}",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @settings.command(name='reset')
    async def settings_reset(self, ctx):
        """Reset all settings"""
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM guild_settings WHERE guild_id = ?', (ctx.guild.id,))
        conn.commit()
        conn.close()
        
        embed = EmbedBuilder.success(
            title="Settings Reset",
            description="All guild settings have been reset to default",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @settings.command(name='config')
    async def settings_config(self, ctx):
        """View current configuration"""
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM guild_settings WHERE guild_id = ?', (ctx.guild.id,))
        result = cursor.fetchone()
        conn.close()
        
        embed = EmbedBuilder.info(
            title="Server Configuration",
            description=f"Settings for {ctx.guild.name}",
            ctx=ctx
        )
        
        if result:
            for i, value in enumerate(result):
                if value and i > 0:
                    embed.add_field(name=f"Setting {i}", value=str(value), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ConfigSettings(bot))
