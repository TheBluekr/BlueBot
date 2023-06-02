import logging
import discord
import typing

from discord import app_commands
from discord.ext import commands

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.buttons"
logger = logging.getLogger(__cogname__)

class Buttons(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        self.logger.info(f"Loaded cog {__cogname__}")
        self.cache = {}
    
    def is_guild_owner():
        async def predicate(ctx):
            return ctx.author == ctx.guild.owner
        return commands.check(predicate)
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if(interaction.type == discord.InteractionType.component):
            if(interaction.data["component_type"] == 2): # Button
                self.logger.info(interaction.data["component_type"])
                data = interaction.data["custom_id"].split(".")
                customid = int(data[1])
                if(data[0] == "role"):
                    role = interaction.guild.get_role(customid)
                    if(interaction.user.get_role(customid) != role):
                        await interaction.user.add_roles(role)
                if(data[0] == "channel"):
                    channel = interaction.guild.get_channel(customid)
                    perms = channel.overwrites_for(interaction.user)
                    perms.view_channel = True
                    await channel.set_permissions(interaction.user, overwrite=perms)
                await interaction.response.defer()

    @is_guild_owner()
    @commands.guild_only()
    @commands.group(pass_context=True)
    async def button(self, ctx):
        pass

    @button.group(pass_context=True)
    async def add(self, ctx):
        pass

    @add.command()
    async def role(self, ctx, message: discord.Message, label: str, style: str, role: discord.Role, emoji: typing.Union[discord.PartialEmoji, discord.Emoji, str]=None):
        view = discord.ui.View.from_message(message)
        style = getattr(discord.ButtonStyle, style)
        view.add_item(discord.ui.Button(label=label, style=style, emoji=emoji, custom_id=f"role.{role.id}"))
        await message.edit(view=view)
    
    @add.command()
    async def channel(self, ctx, message: discord.Message, label: str, style: str, channel: typing.Union[discord.TextChannel, discord.VoiceChannel], emoji: typing.Union[discord.PartialEmoji, discord.Emoji, str]=None):
        view = discord.ui.View.from_message(message)
        style = getattr(discord.ButtonStyle, style)
        view.add_item(discord.ui.Button(label=label, style=style, emoji=emoji, custom_id=f"channel.{channel.id}"))
        await message.edit(view=view)
    
    @add.error
    async def add_error(self, ctx, error):
        if(isinstance(error, commands.errors.MissingRequiredArgument)):
            await ctx.send(f"Missing required argument, please check whether you've provided all required arguments")
        elif(isinstance(error, commands.errors.RoleNotFound)):
            await ctx.send(f"Could not find role with provided id")
        elif(isinstance(error, commands.errors.MessageNotFound)):
            await ctx.send(f"Could not find message with provided id")
    
    @button.command()
    async def url(self, ctx, message: discord.Message, label: str, url: str, emoji: typing.Union[discord.PartialEmoji, discord.Emoji, str]=None):
        view = discord.ui.View.from_message(message)
        view.add_item(discord.ui.Button(label=label, style=discord.ButtonStyle.url, url=url))
        await message.edit(view=view)
    
    @button.command()
    async def clear(self, ctx, message: discord.Message):
        await message.edit(view=None)

    @commands.is_owner()
    @commands.guild_only()
    @commands.command()
    async def sync(self, ctx):
        fmt = await self.bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"Synced {fmt} commands for guild")
    
    @commands.is_owner()
    @commands.command()
    async def globalsync(self, ctx):
        fmt = await self.bot.tree.sync()
        await ctx.send(f"Synced {fmt} commands globally")
    
    @commands.hybrid_command(description="Returns latency of bot")
    async def ping(self, ctx):
        ping1 = f"{str(round(self.bot.latency * 1000))} ms"
        embed = discord.Embed(title= "**Pong!**", description=f"**{ping1}**", color=0xafdafc)
        await ctx.send(embed=embed)
    
async def setup(bot):
    await bot.add_cog(Buttons(bot))