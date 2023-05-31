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

        self.updateChannel = os.getenv("GIT_CHANNEL")

    @tasks.loop(seconds=60)
    async def update_code(self):
        origin = self.repo.remotes.origin
        origin.fetch()
        diff = self.repo.index.diff(origin.refs['Development'].object.hexsha)
        if(len(diff) > 0):
            bShutdown = False

            self.logger.info("File update found on repo, updating files")
            embed = self.bot.embed.create_embed(self.bot.user)
            embed.description = "Files updated in repository:```"
    
            origin.pull()
            for file in diff:
                apath = file.a_path
                apath = apath.replace("/", ".").replace(".py", "")
                if(apath == "bot" or apath.startswith("core.")):
                    # Reboot entire bot to load new bot.py or core/file.py
                    bShutdown = True
                elif(apath.startswith("cogs.")):
                    if(diff.change_type in ["D", "R", "M", "T"]):
                        await self.bot.unload_extension(apath)
                
                bpath = file.b_path
                bpath = bpath.replace("/", ".").replace(".py", "")
                if(bpath.startswith("cogs.")):
                    if(diff.change_type in ["A", "R", "M"]):
                        await self.bot.load_extension(bpath)
                
                # Write to embed what files changed
                if(diff.change_type == "A"):
                    embed.description += f"[Added] {bpath}"
                elif(diff.change_type == "D"):
                    embed.description += f"[Deleted] {apath}"
                elif(diff.change_type == "R"):
                    embed.description += f"[Renamed] {apath} -> {bpath}"
                elif(diff.change_type == "M"):
                    embed.description += f"[Modified] {apath}"
                else:
                    embed.description += f"[Unknown] {diff.change_type} - {apath} - {bpath}"
            
            embed.description += "```"

            channel = await self.bot.fetch_channel(self.updateChannel)
            if(channel != None):
                await channel.send(embed=embed)
            
            if(bShutdown):
                await self.bot.close()