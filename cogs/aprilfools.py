import logging
import discord
import random

from discord.ext import commands, tasks

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.aprilfools"
logger = logging.getLogger(__cogname__)

class Aprilfools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        self.logger.info(f"Loaded cog {__cogname__}")
        self.investor_id = 928570428291682344

    @commands.Cog.listener()
    async def on_message(self, ctx: discord.Message):
        if(ctx.author.id == self.bot.user.id):
            return
        if(ctx.channel.id != 1091484407703019530): # Corporate-discussion channel
            return
        
        randint = random.randint(0, 99) # Range of 0-99 (100 indeces)
        self.logger.info(randint)

        role = ctx.author.get_role(self.investor_id)
        if(role != None and randint < 70):
            await ctx.delete()
        elif(role == None and randint < 80):
            await ctx.delete()
        if(randint == 99):
            await ctx.pin()

async def setup(bot):
    await bot.add_cog(Aprilfools(bot))