import discord
from discord.ext import tasks
import git
import os
import logging

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.core.git"
logger = logging.getLogger(__cogname__)

class Git:
    def __init__(self, bot):
        self.logger = logger

        self.bot = bot
        self.db = bot.db

        self.repo = git.Repo(".")
        self.logger.info("Initialized Git repo")

    @tasks.loop(seconds=60)
    async def update_code(self):
        origin = self.repo.remotes.origin
        origin.fetch()
        diff = self.repo.index.diff(origin.refs['Development'].object.hexsha)
        origin.pull()
        for file in diff:
            apath = file.a_path
            apath = apath.replace("/", ".").replace(".py", "")
            if(apath == "bot" or apath.startswith("core.")):
                # Reboot entire bot to load new bot.py or core/file.py
                exit(1)
            elif(apath.startswith("cogs.")):
                if(diff.change_type in ["D", "R", "M", "T"]):
                    await self.bot.unload_extension(apath)
            
            bpath = file.b_path
            bpath = bpath.replace("/", ".").replace(".py", "")
            if(bpath.startswith("cogs.")):
                if(diff.change_type in ["A", "R", "M"]):
                    await self.bot.load_extension(bpath)