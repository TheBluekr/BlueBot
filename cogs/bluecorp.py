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
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if(interaction.type == discord.InteractionType.component):
            if(interaction.data["component_type"] == 2): # Button
                self.logger.info(interaction.data)
                await interaction.followup.send("This was sent using followup")
                await interaction.response.defer()

    @commands.command()
    async def button(self, ctx):
        view = discord.ui.View()
        button = discord.ui.Button(label="Test", custom_id=f"{self.__class__.__name__}.Test")
        self.logger.info(f"{self.__class__.__name__}.Test")
        view.add_item(button)
        await ctx.send(view=view)
    
async def setup(bot):
    await bot.add_cog(Bluecorp(bot))