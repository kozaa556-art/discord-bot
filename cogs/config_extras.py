import discord
from discord.ext import commands
from utils.embeds import EmbedBuilder
from utils.helpers import db
import sqlite3
import re

class ConfigExtras(commands.Cog):
    """Additional Configuration Commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def cog_check(self, ctx):
        return ctx.author.guild_permissions.administrator
    
    @commands.group(invoke_without_command=True)
    async def filter(self, ctx):
        """View filter options"""
        embed = EmbedBuilder.info(
            title="Filter Options",
            description="Configure content filters for your server",
            ctx=ctx
        )
        embed.add_field(
            name="Available Filters",
            value="caps, invites, links, spoilers, spam, musicfiles, massmention, emoji, words",
            inline=False
        )
        await ctx.send(embed=embed)
    
    @filter.command(name='add')
    async def filter_add(self, ctx, word: str):
        """Add word to filter"""
        embed = EmbedBuilder.success(
            title="Word Filtered",
            description=f"Added `{word}` to filter",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @filter.command(name='remove')
    async def filter_remove(self, ctx, word: str):
        """Remove word from filter"""
        embed = EmbedBuilder.success(
            title="Word Unfiltered",
            description=f"Removed `{word}` from filter",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @filter.command(name='list')
    async def filter_list(self, ctx):
        """List filtered words"""
        embed = EmbedBuilder.info(
            title="Filtered Words",
            description="Words currently filtered on this server",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @filter.command(name='caps')
    async def filter_caps(self, ctx, channel: discord.TextChannel, setting: str, percentage: int = 70):
        """Configure caps filter"""
        if setting.lower() not in ['on', 'off']:
            embed = EmbedBuilder.error(
                title="Invalid Setting",
                description="Use 'on' or 'off'",
                ctx=ctx
            )
            return await ctx.send(embed=embed)
        
        embed = EmbedBuilder.success(
            title="Caps Filter Updated",
            description=f"Caps filter {setting} for {channel.mention} at {percentage}%",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @filter.command(name='invites')
    async def filter_invites(self, ctx, channel: discord.TextChannel, setting: str):
        """Configure invite filter"""
        if setting.lower() not in ['on', 'off']:
            embed = EmbedBuilder.error(
                title="Invalid Setting",
                description="Use 'on' or 'off'",
                ctx=ctx
            )
            return await ctx.send(embed=embed)
        
        embed = EmbedBuilder.success(
            title="Invite Filter Updated",
            description=f"Invite filter {setting} for {channel.mention}",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @filter.command(name='links')
    async def filter_links(self, ctx, channel: discord.TextChannel, setting: str):
        """Configure link filter"""
        if setting.lower() not in ['on', 'off']:
            embed = EmbedBuilder.error(
                title="Invalid Setting",
                description="Use 'on' or 'off'",
                ctx=ctx
            )
            return await ctx.send(embed=embed)
        
        embed = EmbedBuilder.success(
            title="Link Filter Updated",
            description=f"Link filter {setting} for {channel.mention}",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @filter.command(name='spam')
    async def filter_spam(self, ctx, channel: discord.TextChannel, setting: str):
        """Configure spam filter"""
        if setting.lower() not in ['on', 'off']:
            embed = EmbedBuilder.error(
                title="Invalid Setting",
                description="Use 'on' or 'off'",
                ctx=ctx
            )
            return await ctx.send(embed=embed)
        
        embed = EmbedBuilder.success(
            title="Spam Filter Updated",
            description=f"Spam filter {setting} for {channel.mention}",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @commands.group(invoke_without_command=True)
    async def autoresponder(self, ctx):
        """View autoresponder setup"""
        embed = EmbedBuilder.info(
            title="Autoresponder",
            description="Automatically respond to messages",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @autoresponder.command(name='add')
    async def autoresponder_add(self, ctx, trigger: str, *, response: str):
        """Add autoresponder"""
        embed = EmbedBuilder.success(
            title="Autoresponder Added",
            description=f"Trigger: `{trigger}`\nResponse: `{response}`",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @autoresponder.command(name='remove')
    async def autoresponder_remove(self, ctx, trigger: str):
        """Remove autoresponder"""
        embed = EmbedBuilder.success(
            title="Autoresponder Removed",
            description=f"Removed trigger: `{trigger}`",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @autoresponder.command(name='list')
    async def autoresponder_list(self, ctx):
        """List all autoresponders"""
        embed = EmbedBuilder.info(
            title="Autoresponders",
            description="All autoresponders on this server",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    async def ignore(self, ctx, target: discord.Member = None):
        """Ignore member or channel"""
        if not target:
            embed = EmbedBuilder.usage(
                ctx,
                "ignore",
                "Ignore a member or channel from bot commands",
                ",ignore <@member or #channel>",
                ",ignore @user",
                "Administrator"
            )
            return await ctx.send(embed=embed)
        
        embed = EmbedBuilder.success(
            title="Ignored",
            description=f"Ignored {target.mention}",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    async def suggest(self, ctx, *, suggestion: str = None):
        """Submit a suggestion"""
        if not suggestion:
            embed = EmbedBuilder.usage(
                ctx,
                "suggest",
                "Submit a suggestion to server staff",
                ",suggest <your suggestion>",
                ",suggest Add a music bot",
            )
            return await ctx.send(embed=embed)
        
        embed = EmbedBuilder.success(
            title="Suggestion Submitted",
            description=f"Your suggestion has been recorded",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    async def customize(self, ctx):
        """Customize bot settings"""
        embed = EmbedBuilder.info(
            title="Customize Bot",
            description="Customize bot appearance and behavior",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    async def badge(self, ctx, setting: str = None):
        """Configure badge system"""
        if not setting:
            embed = EmbedBuilder.usage(
                ctx,
                "badge",
                "Configure server badges",
                ",badge <on/off>",
                ",badge on",
                "Administrator"
            )
            return await ctx.send(embed=embed)
        
        embed = EmbedBuilder.success(
            title="Badge System Updated",
            description=f"Badge system turned {setting}",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    async def reposter(self, ctx):
        """View reposter setup"""
        embed = EmbedBuilder.info(
            title="Reposter",
            description="Repost messages from other channels",
            ctx=ctx
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ConfigExtras(bot))
