import logging
import discord

from discord.ext import commands, tasks

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.presence"
logger = logging.getLogger(__cogname__)

class Presence(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        self.logger.info(f"Loaded cog {__cogname__}")
        
        self.async_init.start()
    
    @tasks.loop(count=1)
    async def async_init(self):
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="users"))

    @commands.group(pass_context=True)
    @commands.is_owner()
    async def activity(self, ctx):
        pass

    @activity.command()
    async def play(self, ctx, *, arg):
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=arg))
    
    @activity.command()
    async def stream(self, ctx, *, arg):
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.streaming, name=arg))
    
    @activity.command()
    async def listen(self, ctx, *, arg):
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=arg))
    
    @activity.command()
    async def watch(self, ctx, *, arg):
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=arg))
    
async def setup(bot):
    await bot.add_cog(Presence(bot))