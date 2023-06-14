import discord
from discord.ext import tasks
from discord.ext.commands import ExtensionFailed
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
        diff = self.repo.index.diff(origin.refs[os.getenv("GIT_BRANCH")].object.hexsha)
        if(len(diff) > 0):
            bShutdown = False

            self.logger.info("File update found on repo, updating files")
            embed = self.bot.embed.create_embed(self.bot.user)
            embed.description = "Files updated in repository:```"

            channel = await self.bot.fetch_channel(self.updateChannel)    

            origin.pull()
            for file in diff:
                apath = file.a_path
                apath = apath.replace("/", ".").replace(".py", "")
                if(apath == "bot" or apath.startswith("core.")):
                    # Reboot entire bot to load new bot.py or core/file.py
                    self.logger.info("Core code updated, marking for reboot")
                    bShutdown = True
                elif(apath.startswith("cogs.") and apath.count(".") == 1):
                    if(file.change_type in ["D", "R", "M"]):
                        await self.bot.unload_extension(apath)
                
                bpath = file.b_path
                bpath = bpath.replace("/", ".").replace(".py", "")
                if(bpath.startswith("cogs.") and bpath.count(".") == 1):
                    if(file.change_type in ["A", "R", "M"]):
                        try:
                            await self.bot.load_extension(bpath)
                        except ExtensionFailed as err:
                            self.logger.error(f"{err.name}: {err.original}")
                            errorEmbed = self.bot.embed.create_embed(self.bot.user)
                            embed.description = f"Error occured in {err.name}:\n```{err.original}```"
                            if(channel != None):
                                await channel.send(embed=errorEmbed)
                
                if(file.change_type == "A"):
                    embed.description += f"[Added] {file.b_path}"
                elif(file.change_type == "D"):
                    embed.description += f"[Deleted] {file.a_path}"
                elif(file.change_type == "R"):
                    embed.description += f"[Renamed] {file.a_path} -> {file.b_path}"
                elif(file.change_type == "M"):
                    embed.description += f"[Modified] {file.a_path}"
                else:
                    embed.description += f"[Unknown] {diff.change_type} - {file.a_path} - {file.b_path}"
            
            embed.description += "```"

            if(channel != None):
                await channel.send(embed=embed)
            
            if(bShutdown):
                await self.bot.close()