import discord
from discord.ext import commands, tasks
from utils.embeds import EmbedBuilder
from utils.helpers import db, TimeParser, PermissionChecker
import sqlite3
from datetime import datetime, timedelta
import asyncio

class Moderation(commands.Cog):
    """Moderation Commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.timers = {}
    
    async def cog_check(self, ctx):
        """Check if user has mod permissions"""
        return ctx.author.guild_permissions.ban_members or ctx.author.guild_permissions.moderate_members
    
    def create_case(self, guild_id: int, user_id: int, moderator_id: int, action: str, reason: str, duration: str = None):
        """Create moderation case"""
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO cases (guild_id, user_id, moderator_id, action, reason, duration)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (guild_id, user_id, moderator_id, action, reason, duration))
        conn.commit()
        case_id = cursor.lastrowid
        conn.close()
        return case_id
    
    async def log_moderation(self, ctx, action: str, user: discord.User, reason: str = None, duration: str = None):
        """Log moderation action"""
        case_id = self.create_case(ctx.guild.id, user.id, ctx.author.id, action, reason or "No reason", duration)
        
        # Send to modlog
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT modlog_channel FROM guild_settings WHERE guild_id = ?', (ctx.guild.id,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            modlog = self.bot.get_channel(result[0])
            if modlog:
                embed = EmbedBuilder.warning(
                    title=f"{action.title()} | Case #{case_id}",
                    description=f"User: {user.mention}\nModerator: {ctx.author.mention}\nReason: {reason or 'No reason'}"
                )
                if duration:
                    embed.add_field(name="Duration", value=duration, inline=False)
                await modlog.send(embed=embed)
    
    @commands.command()
    async def tempban(self, ctx, user: discord.User, duration: str, *, reason: str = None):
        """Temporarily ban a user"""
        time_delta = TimeParser.parse_duration(duration)
        if not time_delta:
            embed = EmbedBuilder.usage(
                ctx,
                "tempban",
                "Temporarily ban a user from the server",
                ",tempban <@user> <duration> [reason]",
                ",tempban @user 7d Spamming",
                "Ban Members"
            )
            return await ctx.send(embed=embed)
        
        try:
            await ctx.guild.ban(user, reason=reason or "No reason provided")
            await self.log_moderation(ctx, "tempban", user, reason, duration)
            
            # Schedule unban
            unban_time = datetime.utcnow() + time_delta
            self.timers[f"unban_{ctx.guild.id}_{user.id}"] = unban_time
            
            await ctx.message.add_reaction('👍')
        except discord.Forbidden:
            embed = EmbedBuilder.error(
                title="Permission Denied",
                description="I don't have permission to ban this user",
                ctx=ctx
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    async def warn(self, ctx, member: discord.Member, *, reason: str = None):
        """Warn a user"""
        await self.log_moderation(ctx, "warn", member, reason)
        
        # Update warning count
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (user_id, guild_id, warnings) VALUES (?, ?, 1)
            ON CONFLICT(user_id, guild_id) DO UPDATE SET warnings = warnings + 1
        ''', (member.id, ctx.guild.id))
        conn.commit()
        cursor.execute('SELECT warnings FROM users WHERE user_id = ? AND guild_id = ?', (member.id, ctx.guild.id))
        warns = cursor.fetchone()[0]
        conn.close()
        
        await ctx.message.add_reaction('👍')
        
        try:
            embed = EmbedBuilder.warning(
                title="You have been warned",
                description=f"Server: {ctx.guild.name}\nReason: {reason or 'No reason'}\nWarnings: {warns}"
            )
            await member.send(embed=embed)
        except:
            pass
    
    @commands.command()
    async def ban(self, ctx, user: discord.User, delete_history: int = 0, *, reason: str = None):
        """Ban a user"""
        try:
            await ctx.guild.ban(user, delete_message_days=delete_history, reason=reason or "No reason")
            await self.log_moderation(ctx, "ban", user, reason)
            await ctx.message.add_reaction('👍')
        except discord.Forbidden:
            embed = EmbedBuilder.error(
                title="Permission Denied",
                description="I don't have permission to ban this user",
                ctx=ctx
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    async def unban(self, ctx, user: discord.User, *, reason: str = None):
        """Unban a user"""
        try:
            await ctx.guild.unban(user, reason=reason or "No reason")
            await self.log_moderation(ctx, "unban", user, reason)
            await ctx.message.add_reaction('👍')
        except discord.Forbidden:
            embed = EmbedBuilder.error(
                title="Permission Denied",
                description="I don't have permission to unban users",
                ctx=ctx
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    async def hardban(self, ctx, user: discord.User, *, reason: str = None):
        """Permanently ban a user"""
        try:
            await ctx.guild.ban(user, delete_message_days=7, reason=reason or "Hardban")
            await self.log_moderation(ctx, "hardban", user, reason)
            await ctx.message.add_reaction('👍')
        except discord.Forbidden:
            embed = EmbedBuilder.error(
                title="Permission Denied",
                description="I don't have permission to ban this user",
                ctx=ctx
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    async def softban(self, ctx, member: discord.Member, delete_history: int = 0, *, reason: str = None):
        """Softban (ban and immediately unban) a user"""
        try:
            await ctx.guild.ban(member, delete_message_days=delete_history, reason=reason or "Softban")
            await asyncio.sleep(0.5)
            await ctx.guild.unban(member, reason="Softban - messages deleted")
            await self.log_moderation(ctx, "softban", member, reason)
            await ctx.message.add_reaction('👍')
        except discord.Forbidden:
            embed = EmbedBuilder.error(
                title="Permission Denied",
                description="I don't have permission to softban this user",
                ctx=ctx
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        """Kick a member"""
        try:
            await ctx.guild.kick(member, reason=reason or "No reason")
            await self.log_moderation(ctx, "kick", member, reason)
            await ctx.message.add_reaction('👍')
        except discord.Forbidden:
            embed = EmbedBuilder.error(
                title="Permission Denied",
                description="I don't have permission to kick this member",
                ctx=ctx
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    async def timeout(self, ctx, member: discord.Member, duration: str, *, reason: str = None):
        """Timeout a member"""
        time_delta = TimeParser.parse_duration(duration)
        if not time_delta or time_delta.total_seconds() > 2419200:
            embed = EmbedBuilder.error(
                title="Invalid Duration",
                description="Timeout duration must be between 1 second and 28 days",
                ctx=ctx
            )
            return await ctx.send(embed=embed)
        
        try:
            await member.timeout(time_delta, reason=reason or "No reason")
            await self.log_moderation(ctx, "timeout", member, reason, duration)
            await ctx.message.add_reaction('👍')
        except discord.Forbidden:
            embed = EmbedBuilder.error(
                title="Permission Denied",
                description="I don't have permission to timeout this member",
                ctx=ctx
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    async def untimeout(self, ctx, member: discord.Member, *, reason: str = None):
        """Remove timeout from member"""
        try:
            await member.timeout(None, reason=reason or "Timeout removed")
            await self.log_moderation(ctx, "untimeout", member, reason)
            await ctx.message.add_reaction('👍')
        except discord.Forbidden:
            embed = EmbedBuilder.error(
                title="Permission Denied",
                description="I don't have permission to remove timeout",
                ctx=ctx
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    async def mute(self, ctx, member: discord.Member, duration: str = None, *, reason: str = None):
        """Mute a member"""
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT muted_role FROM guild_settings WHERE guild_id = ?', (ctx.guild.id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[0]:
            embed = EmbedBuilder.error(
                title="Muted Role Not Set",
                description="Please set a muted role with `,settings muted @role`",
                ctx=ctx
            )
            return await ctx.send(embed=embed)
        
        mute_role = ctx.guild.get_role(result[0])
        if not mute_role:
            embed = EmbedBuilder.error(
                title="Muted Role Not Found",
                description="The configured muted role no longer exists",
                ctx=ctx
            )
            return await ctx.send(embed=embed)
        
        try:
            await member.add_roles(mute_role, reason=reason or "Muted")
            await self.log_moderation(ctx, "mute", member, reason, duration)
            await ctx.message.add_reaction('👍')
        except discord.Forbidden:
            embed = EmbedBuilder.error(
                title="Permission Denied",
                description="I don't have permission to mute this member",
                ctx=ctx
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    async def unmute(self, ctx, member: discord.Member, *, reason: str = None):
        """Unmute a member"""
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT muted_role FROM guild_settings WHERE guild_id = ?', (ctx.guild.id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[0]:
            embed = EmbedBuilder.error(
                title="Muted Role Not Set",
                description="Please set a muted role with `,settings muted @role`",
                ctx=ctx
            )
            return await ctx.send(embed=embed)
        
        mute_role = ctx.guild.get_role(result[0])
        if not mute_role:
            return
        
        try:
            await member.remove_roles(mute_role, reason=reason or "Unmuted")
            await self.log_moderation(ctx, "unmute", member, reason)
            await ctx.message.add_reaction('👍')
        except discord.Forbidden:
            embed = EmbedBuilder.error(
                title="Permission Denied",
                description="I don't have permission to unmute this member",
                ctx=ctx
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    async def imute(self, ctx, member: discord.Member, *, reason: str = None):
        """Image mute a member"""
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT immute_role FROM guild_settings WHERE guild_id = ?', (ctx.guild.id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[0]:
            embed = EmbedBuilder.error(
                title="Image Mute Role Not Set",
                description="Please configure an image mute role",
                ctx=ctx
            )
            return await ctx.send(embed=embed)
        
        await self.log_moderation(ctx, "imute", member, reason)
        await ctx.message.add_reaction('👍')
    
    @commands.command()
    async def iunmute(self, ctx, member: discord.Member, *, reason: str = None):
        """Remove image mute from member"""
        await self.log_moderation(ctx, "iunmute", member, reason)
        await ctx.message.add_reaction('👍')
    
    @commands.command()
    async def rmute(self, ctx, member: discord.Member, *, reason: str = None):
        """Reaction mute a member"""
        await self.log_moderation(ctx, "rmute", member, reason)
        await ctx.message.add_reaction('👍')
    
    @commands.command()
    async def runmute(self, ctx, member: discord.Member, *, reason: str = None):
        """Remove reaction mute from member"""
        await self.log_moderation(ctx, "runmute", member, reason)
        await ctx.message.add_reaction('👍')
    
    @commands.command()
    async def jail(self, ctx, member: discord.Member, duration: str = None, *, reason: str = None):
        """Jail a member"""
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT jail_role FROM guild_settings WHERE guild_id = ?', (ctx.guild.id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[0]:
            embed = EmbedBuilder.error(
                title="Jail Role Not Set",
                description="Please set a jail role with `,settings jailrole @role`",
                ctx=ctx
            )
            return await ctx.send(embed=embed)
        
        jail_role = ctx.guild.get_role(result[0])
        if jail_role:
            try:
                await member.add_roles(jail_role, reason=reason or "Jailed")
                await self.log_moderation(ctx, "jail", member, reason, duration)
                await ctx.message.add_reaction('👍')
            except discord.Forbidden:
                embed = EmbedBuilder.error(
                    title="Permission Denied",
                    description="I don't have permission to jail this member",
                    ctx=ctx
                )
                await ctx.send(embed=embed)
    
    @commands.command()
    async def unjail(self, ctx, member: discord.Member, *, reason: str = None):
        """Unjail a member"""
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT jail_role FROM guild_settings WHERE guild_id = ?', (ctx.guild.id,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            jail_role = ctx.guild.get_role(result[0])
            if jail_role:
                try:
                    await member.remove_roles(jail_role, reason=reason or "Unjailed")
                    await self.log_moderation(ctx, "unjail", member, reason)
                    await ctx.message.add_reaction('👍')
                except discord.Forbidden:
                    embed = EmbedBuilder.error(
                        title="Permission Denied",
                        description="I don't have permission to unjail this member",
                        ctx=ctx
                    )
                    await ctx.send(embed=embed)
    
    @commands.command()
    async def warnings(self, ctx, member: discord.Member):
        """View member warnings"""
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT warnings FROM users WHERE user_id = ? AND guild_id = ?', (member.id, ctx.guild.id))
        result = cursor.fetchone()
        conn.close()
        
        warnings = result[0] if result else 0
        embed = EmbedBuilder.info(
            title=f"Warnings for {member}",
            description=f"Total warnings: {warnings}",
            ctx=ctx
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    async def history(self, ctx, member: discord.Member = None):
        """View member moderation history"""
        if not member:
            embed = EmbedBuilder.usage(
                ctx,
                "history",
                "View moderation history for a member",
                ",history <@member>",
                ",history @user",
                "Moderate Members"
            )
            return await ctx.send(embed=embed)
        
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cases WHERE guild_id = ? AND user_id = ? ORDER BY case_id DESC LIMIT 10', (ctx.guild.id, member.id))
        cases = cursor.fetchall()
        conn.close()
        
        embed = EmbedBuilder.info(
            title=f"Moderation History - {member}",
            description=f"Recent cases for {member.mention}",
            ctx=ctx
        )
        
        for case in cases:
            embed.add_field(
                name=f"Case #{case[0]} - {case[4]}",
                value=f"Reason: {case[5]}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command()
    async def role(self, ctx, member: discord.Member = None, role: discord.Role = None, action: str = None):
        """Manage member roles"""
        if not member or not role:
            embed = EmbedBuilder.usage(
                ctx,
                "role",
                "Add or remove roles from members",
                ",role <@member> <@role>",
                ",role @user @Members",
                "Manage Roles"
            )
            return await ctx.send(embed=embed)
        
        try:
            if role not in member.roles:
                await member.add_roles(role)
                embed = EmbedBuilder.success(
                    title="Role Added",
                    description=f"Added {role.mention} to {member.mention}",
                    ctx=ctx
                )
            else:
                await member.remove_roles(role)
                embed = EmbedBuilder.success(
                    title="Role Removed",
                    description=f"Removed {role.mention} from {member.mention}",
                    ctx=ctx
                )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = EmbedBuilder.error(
                title="Permission Denied",
                description="I don't have permission to manage roles",
                ctx=ctx
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    async def purge(self, ctx, amount: int = None):
        """Purge messages"""
        if not amount:
            embed = EmbedBuilder.usage(
                ctx,
                "purge",
                "Delete messages from a channel",
                ",purge <amount>",
                ",purge 50",
                "Manage Messages"
            )
            return await ctx.send(embed=embed)
        
        try:
            deleted = await ctx.channel.purge(limit=amount)
            embed = EmbedBuilder.success(
                title="Messages Purged",
                description=f"Deleted {len(deleted)} messages",
                ctx=ctx
            )
            msg = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await msg.delete()
        except discord.Forbidden:
            embed = EmbedBuilder.error(
                title="Permission Denied",
                description="I don't have permission to delete messages",
                ctx=ctx
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    async def slowmode(self, ctx, channel: discord.TextChannel = None, delay: int = None):
        """Set channel slowmode"""
        target = channel or ctx.channel
        
        try:
            if delay:
                await target.edit(slowmode_delay=delay)
                embed = EmbedBuilder.success(
                    title="Slowmode Enabled",
                    description=f"Slowmode set to {delay} seconds in {target.mention}",
                    ctx=ctx
                )
            else:
                await target.edit(slowmode_delay=0)
                embed = EmbedBuilder.success(
                    title="Slowmode Disabled",
                    description=f"Slowmode disabled in {target.mention}",
                    ctx=ctx
                )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = EmbedBuilder.error(
                title="Permission Denied",
                description="I don't have permission to edit this channel",
                ctx=ctx
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    async def lockdown(self, ctx, channel: discord.TextChannel = None, *, reason: str = None):
        """Lockdown a channel"""
        target = channel or ctx.channel
        
        try:
            for role in target.guild.roles:
                if role.name != "@everyone":
                    await target.set_permissions(role, send_messages=False)
            
            embed = EmbedBuilder.success(
                title="Channel Locked",
                description=f"{target.mention} is now locked",
                ctx=ctx
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = EmbedBuilder.error(
                title="Permission Denied",
                description="I don't have permission to lock this channel",
                ctx=ctx
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    async def unlock(self, ctx, channel: discord.TextChannel = None, *, reason: str = None):
        """Unlock a channel"""
        target = channel or ctx.channel
        
        try:
            await target.set_permissions(ctx.guild.default_role, send_messages=True)
            embed = EmbedBuilder.success(
                title="Channel Unlocked",
                description=f"{target.mention} is now unlocked",
                ctx=ctx
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = EmbedBuilder.error(
                title="Permission Denied",
                description="I don't have permission to unlock this channel",
                ctx=ctx
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    async def modstats(self, ctx, member: discord.Member = None):
        """View moderation statistics"""
        target = member or ctx.author
        
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        cursor.execute('SELECT action, COUNT(*) FROM cases WHERE guild_id = ? AND user_id = ? GROUP BY action', (ctx.guild.id, target.id))
        stats = cursor.fetchall()
        conn.close()
        
        embed = EmbedBuilder.info(
            title=f"Moderation Stats - {target}",
            description=f"Statistics for {target.mention}",
            ctx=ctx
        )
        
        for action, count in stats:
            embed.add_field(name=action.title(), value=str(count), inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
