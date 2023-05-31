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

        # self.update_code.start()
        self.logger.info(f"{self.repo.head.object.hexsha}")
        origin = self.repo.remotes.origin
        origin.fetch()
        self.logger.info(f"{origin.refs['Development'].object.hexsha}")
        diff = self.repo.index.diff(origin.refs['Development'].object.hexsha)
        origin.pull()
        self.logger.info(f"{diff}")
        for file in diff:
            path = file.a_path
            path = path.replace("/", ".").replace(".py", "")
            if(path == "bot" or path.startswith("core.")):
                # Reboot entire bot to load new bot.py or core/file.py
                pass
            elif(path.startswith("cogs.")):
                self.bot.unload_extension(path)
                self.bot.load_extension(path)
            self.logger.info(path)
    
    @tasks.loop(seconds=60)
    async def update_code(self):
        self.logger.info(f"{self.repo.head.object.hexsha}")
        origin = self.repo.remotes.origin
        origin.fetch()
        self.logger.info(f"{origin.refs['Development'].object.hexsha}")