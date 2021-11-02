import logging
import discord
import asyncio

from discord import audit_logs

from redbot.core import commands, Config, checks
from redbot.core.utils.predicates import MessagePredicate
from typing import Optional, List

try:
    from redbot.core.commands import GuildContext
except ImportError:
    from redbot.core.commands import Context as GuildContext

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.toxburn"
logger = logging.getLogger(__cogname__)

class Toxburn(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.logger = logger
        self.config = Config.get_conf(self, identifier=154647815, force_registration=True)

        default_role = {"streamable": False, "DISALLOWED_CHANNELS": []}
        default_user = {"streamable": False, "ALLOWED_CHANNELS": []}

        self.config.register_role(**default_role)
        self.config.register_user(**default_user)

    # Commands
    @commands.guild_only()
    @checks.mod_or_permissions(manage_roles=True)
    @commands.group(name="streamperms", autohelp=True)
    async def streamperms(self, ctx: GuildContext):
        """Sets permission for role/user to stream in voice"""
        pass

    @streamperms.group(name="role")
    async def stream_role(self, ctx: GuildContext):
        """
        Manage a role settings 
        """
        pass

    @stream_role.command(name="set")
    @checks.admin_or_permissions(manage_roles=True)
    async def set_role(self, ctx: GuildContext, role: discord.Role, enabled: bool):
        """
        Sets role to be able to stream in channels
        """
        if not enabled:
            if await self.config.role(role).DISALLOWED_CHANNELS():
                pred = MessagePredicate.yes_or_no(ctx)
                await ctx.maybe_send_embed(f"Found channels for role {role}, do you want to erase them?")
                try:
                    await self.bot.wait_for("message", check=pred, timeout=30)
                except asyncio.TimeoutError:
                    return await ctx.send("Timed out.")
                if pred.result:
                    await self.config.role(role).DISALLOWED_CHANNELS.set([])

            await self.config.role(role).streamable.set(False)
            await ctx.tick()
        else:
            await self.config.role(role).streamable.set(True)
            await ctx.tick()
    
    @stream_role.group("channel")
    @checks.admin_or_permissions(manage_roles=True)
    async def stream_role_channel(self, ctx: GuildContext):
        """
        Manage channels for a specified role 
        """
        pass

    @stream_role_channel.command(name="add")
    async def add_role_channel(self, ctx: GuildContext, role: discord.Role, channel: discord.VoiceChannel):
        """
        Adds a channel to the disallowed list of channels for a specified role
        """
        if not await self.config.role(role).streamable():
            return await ctx.maybe_send_embed("Role isn't set as allowed to stream.")

        data = await self.config.role(role).DISALLOWED_CHANNELS()

        if channel.id in data:
            return await ctx.maybe_send_embed("Channel is already disallowed.")
        
        data.append(channel.id)

        await self.config.role(role).DISALLOWED_CHANNELS.set(data)
        await ctx.tick()

    @stream_role_channel.command(name="remove")
    async def remove_role_channel(self, ctx: GuildContext, role: discord.Role, channel: discord.VoiceChannel):
        """
        Removes a channel from the disallowed list of channels for a specified role
        """
        if not await self.config.role(role).streamable():
            return await ctx.maybe_send_embed("Role isn't set as allowed to stream.")

        data = await self.config.role(role).DISALLOWED_CHANNELS()

        if channel.id not in data:
            return await ctx.maybe_send_embed("Channel is already permitted.")
        
        data.remove(channel.id)

        await self.config.role(role).DISALLOWED_CHANNELS.set(data)
        await ctx.tick()

    @streamperms.group(name="user")
    async def stream_user(self, ctx: GuildContext):
        """
        Manage user settings 
        """
        pass

    @stream_user.command(name="set")
    @checks.admin_or_permissions(manage_roles=True)
    async def set_user(self, ctx: GuildContext, user: discord.Member, enabled: bool):
        """
        Sets user to be able to stream in channels
        """
        if not enabled:
            if await self.config.user(user).ALLOWED_CHANNELS():
                pred = MessagePredicate.yes_or_no(ctx)
                await ctx.maybe_send_embed(f"Found channels for user {user}, do you want to erase them?")
                try:
                    await self.bot.wait_for("message", check=pred, timeout=30)
                except asyncio.TimeoutError:
                    return await ctx.send("Timed out.")
                if pred.result:
                    await self.config.user(user).ALLOWED_CHANNELS.set([])

            await self.config.user(user).streamable.set(False)
            await ctx.tick()
        else:
            await self.config.user(user).streamable.set(True)
            await ctx.tick()
    
    @stream_user.group("channel")
    @checks.admin_or_permissions(manage_roles=True)
    async def stream_user_channel(self, ctx: GuildContext):
        """
        Manage channels for a specified role 
        """
        pass

    @stream_user_channel.command(name="add")
    async def add_user_channel(self, ctx: GuildContext, user: discord.Member, channel: discord.VoiceChannel):
        """
        Adds a channel to the allowed list of channels for a specified user
        """
        if not await self.config.role(user).streamable():
            return await ctx.maybe_send_embed("User isn't set as allowed to stream.")

        data = await self.config.role(user).ALLOWED_CHANNELS()

        if channel.id in data:
            return await ctx.maybe_send_embed("Channel is already permitted.")
        
        data.append(channel.id)

        await self.config.role(user).ALLOWED_CHANNELS.set(data)
        await ctx.tick()

    @stream_user_channel.command(name="remove")
    async def remove_user_channel(self, ctx: GuildContext, user: discord.Member, channel: discord.VoiceChannel):
        """
        Removes a channel from the allowed list of channels for a specified user
        """
        if not await self.config.user(user).streamable():
            return await ctx.maybe_send_embed("User isn't set as allowed to stream.")

        data = await self.config.user(user).DISALLOWED_CHANNELS()

        if channel.id not in data:
            return await ctx.maybe_send_embed("Channel is already disallowed.")
        
        data.remove(channel.id)

        await self.config.user(user).DISALLOWED_CHANNELS.set(data)
        await ctx.tick()
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if(message.channel.id == 514750971759558666):
            await message.add_reaction("💚")
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, member):
        if(reaction.message.channel.id == 546003196414525450):
            if(str(reaction.emoji) == "✅"):
                # Send dm with link to google form
                await member.create_dm()
                await member.send("https://forms.gle/cUYR6LNybwr89jWn6")
                await reaction.remove(member)
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if(member.guild.id != 512823554698641408):
            return
        if not after.self_stream:
            return
        if(after.channel == None):
            return
        if await self.config.user(member).streamable() and after.channel.id in await self.config.user(member).ALLOWED_CHANNELS():
            pass
        else:
            for role in member.roles:
                if await self.config.role(role).streamable() and after.channel.id not in await self.config.role(role).DISALLOWED_CHANNELS():
                    return
        await member.move_to(None, reason="Attempted streaming while missing streaming role")
        await member.create_dm()
        await member.send("Sorry, you don't have the permissions needed to stream in voice channels! 💚")