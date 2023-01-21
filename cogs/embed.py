import discord
import logging
from discord.ext import commands

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.embed"
logger = logging.getLogger(__cogname__)

class EmbedColorCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        self.logger.info(f"Loaded cog {__cogname__}")

        self.db = self.bot.db
        self.embed_colors = self.bot.embed_colors
    
    @commands.command(aliases=["embedcolour"])
    async def embedcolor(self, ctx, color: discord.Colour):
        self.embed_colors.set_color(ctx.author, color)
        await ctx.send(embed=discord.Embed(color=color, description=f"Set personal embed color to: #{color.value:0>6X}"))
        
    @embedcolor.error
    async def embedcolor_error(self, ctx, error):
        if(isinstance(error, commands.CheckFailure)):
            return

async def setup(bot):
    await bot.add_cog(EmbedColorCommands(bot))