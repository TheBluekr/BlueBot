import git
import discord
from discord.ext import tasks
import logging

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.core.git"
logger = logging.getLogger(__cogname__)

class Git:
    def __init__(self, bot):
        self.logger = logger

        self.bot = bot
        self.db = bot.db
    
    @tasks.loop(seconds=60)
    async def update_code(self):
        pass