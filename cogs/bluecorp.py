import logging
import discord
import asyncio
import aiohttp

from discord.ext import commands, tasks

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.bluecorp"
logger = logging.getLogger(__cogname__)

class Bluecorp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        self.logger.info(f"Loaded cog {__cogname__}")
    
async def setup(bot):
    await bot.add_cog(Bluecorp(bot))