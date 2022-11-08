import logging
from unicodedata import name
import discord
import asyncio
import aiohttp

from discord.ext import commands, tasks

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.ban"
logger = logging.getLogger(__cogname__)

def canBan():
    async def predicate(ctx):
        permissions = ctx.channel.permissions_for(ctx.author)
        return permissions.ban_members
    return commands.check(predicate)

class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        self.logger.info(f"Loaded cog {__cogname__}")
    
    @commands.command()
    @canBan()
    async def ban(self, ctx, user: discord.User, *, reason: str="None supplied.", days: int=0):
        """Bans a user from the guild"""
        await ctx.guild.ban(user, reason=f"Banned by: {ctx.author}. Reason: {reason}", delete_message_days=days)
        embed = discord.Embed(description=f"Succesfully banned user: {user}")
        embed.set_footer(text=f"Banned by: {ctx.author}", icon_url=ctx.author.avatar.url)
        embed.color = ctx.author.color
        await ctx.send(embed=embed)
    
async def setup(bot):
    await bot.add_cog(Ban(bot))