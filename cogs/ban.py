import logging
from unicodedata import name
import discord

from discord import app_commands
from discord.ext import commands

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.ban"
logger = logging.getLogger(__cogname__)

def can_ban():
    async def predicate(ctx):
        permissions = ctx.channel.permissions_for(ctx.author)
        return permissions.ban_members
    return commands.check(predicate)

class BanFlags(commands.FlagConverter):
    user: discord.User = commands.flag(description="User to ban from guild")
    reason: str = commands.flag(default="", description="Reason for the ban")
    days: int = commands.flag(default=1, description="Numbers of days worth of messages to delete")

class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        self.logger.info(f"Loaded cog {__cogname__}")
    
    @commands.hybrid_command()
    @can_ban()
    async def banuser(self, ctx, *, flags: BanFlags):
        """Bans a user from the guild"""
        await ctx.guild.ban(flags.user, reason=f"Banned by: {ctx.author}. Reason: {flags.reason}", delete_message_days=flags.days)
        embed = discord.Embed(description=f"Succesfully banned user: {flags.user}")
        embed.set_footer(text=f"Banned by: {ctx.author}", icon_url=ctx.author.avatar.url)
        embed.color = ctx.author.color
        await ctx.send(embed=embed)
    
async def setup(bot):
    await bot.add_cog(Ban(bot))