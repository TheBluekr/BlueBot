import discord
import logging
from discord.ext import commands
from typing import Union

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.embed"
logger = logging.getLogger(__cogname__)

class EmbedColorCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        self.logger.info(f"Loaded cog {__cogname__}")

        self.db = self.bot.db
        self.embed = self.bot.embed
    
    @commands.group(aliases=["embedcolour"])
    async def embedcolor(self, ctx):
        embed = self.embed.create_embed(ctx.author)
        color = self.embed.get_color(ctx.author)
        embed.description = f"Your personal embed color is: #{color.value:0>6X}"
        await ctx.send(embed=embed)
    
    @embedcolor.command()
    async def set(self, ctx, color: discord.Colour):
        self.embed.set_color(ctx.author, color)
        embed = self.embed.create_embed(ctx.author)
        embed.description = f"Set personal embed color to: #{color.value:0>6X}"
        await ctx.send(embed=embed)
        
    @embedcolor.error
    async def embedcolor_error(self, ctx, error):
        if(isinstance(error, commands.CheckFailure)):
            return

async def setup(bot):
    await bot.add_cog(EmbedColorCommands(bot))