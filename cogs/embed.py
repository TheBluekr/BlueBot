import discord
import logging
from discord.ext import commands
from discord import app_commands
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
    
    embed = app_commands.Group(name="embed", description="Personalize embed color for embeds returned from invoking commands")

    @embed.command()
    async def get(self, interaction: discord.Interaction):
        embed = self.embed.create_embed(interaction.user)
        color = self.embed.get_color(interaction.user)
        embed.description = f"Your personal embed color is: #{color.value:0>6X}"
        await interaction.response.send_message(embed=embed)
    
    @embed.command()
    async def set(self, interaction: discord.Interaction, color: str):
        embed = self.embed.create_embed(interaction.user)
        try:
            colorcls = discord.Color.from_str(color)
            self.embed.set_color(interaction.user, colorcls)
            embed.color = colorcls
            embed.description = embed.description = f"Set personal embed color to: #{colorcls.value:0>6X}"
        except ValueError as err:
            self.logger.error(err)
            embed.description = f"Invalid color format provided"
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(EmbedColorCommands(bot))