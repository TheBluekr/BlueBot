import logging
import discord
import typing
import re

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
        self.embed = self.bot.embed
        
        self.cache = {}
    
    def is_guild_owner():
        async def predicate(ctx):
            return ctx.author == ctx.guild.owner
        return commands.check(predicate)
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if(interaction.type == discord.InteractionType.component):
            if(interaction.data["component_type"] == 2): # Button
                data = interaction.data["custom_id"].split(".")
                customid = int(data[1])
                if(data[0] == "role"):
                    role = interaction.guild.get_role(customid)
                    if(role):
                        if(interaction.user.get_role(customid) != role):
                            await interaction.user.add_roles(role)
                        else:
                            await interaction.user.remove_roles(role)
                if(data[0] == "channel"):
                    channel = interaction.guild.get_channel(customid)
                    perms = channel.overwrites_for(interaction.user)
                    perms.view_channel = not perms.view_channel
                    await channel.set_permissions(interaction.user, overwrite=perms)
                await interaction.response.defer()

    button = app_commands.Group(name="button", description="Manage buttons on messages")
    
    @button.command()
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.choices(style=[app_commands.Choice(name="primary", value="primary"),
                                app_commands.Choice(name="secondary", value="secondary"),
                                app_commands.Choice(name="success", value="success"),
                                app_commands.Choice(name="danger", value="danger"),
                                app_commands.Choice(name="link", value="link"),
                                app_commands.Choice(name="blurple", value="primary"),
                                app_commands.Choice(name="grey", value="secondary"),
                                app_commands.Choice(name="gray", value="secondary"),
                                app_commands.Choice(name="green", value="success"),
                                app_commands.Choice(name="red", value="danger"),
                                app_commands.Choice(name="url", value="link")])
    @app_commands.choices(type=[app_commands.Choice(name="Role", value="role"),
                                app_commands.Choice(name="Channel", value="channel"),
                                app_commands.Choice(name="URL", value="url")])
    async def add(self, interaction: discord.Interaction, message: str, style: app_commands.Choice[str], type: app_commands.Choice[str], value: str, label: str=None, emoji: str=None):
        message = await interaction.channel.fetch_message(int(message))
        view = discord.ui.View.from_message(message)
        style = getattr(discord.ButtonStyle, style.value)

        embed = self.embed.create_embed(interaction.user)

        if(message == None):
            embed.description = "```Failed to find message```"
            return await interaction.response.send_message(embed=embed)

        if(type.value == "role"):
            match = re.compile(r'([0-9]{15,20})$').match(value) or re.match(r'<@&([0-9]{15,20})>$', value)
            if match:
                role = interaction.guild.get_role(int(match.group(1)))
            else:
                role = discord.utils.get(interaction.guild.roles, name=value)
            if role is None:
                return await interaction.response.send_message("No role found")
            view.add_item(discord.ui.Button(label=label, style=style, emoji=emoji, custom_id=f"role.{role.id}"))
        elif(type.value == "channel"):
            match = re.compile(r'([0-9]{15,20})$').match(value) or re.match(r'<#([0-9]{15,20})>$', value)
            channel = None
            guild = interaction.guild

            if(match == None):
                channel = discord.utils.get(guild.channels, name=value)
            else:
                channel_id = int(match.group(1))
                channel = guild.get_channel(channel_id)

            if(channel == None):
                embed.description = "```Failed to find channel```"
                return await interaction.response.send_message(embed=embed)
            view.add_item(discord.ui.Button(label=label, style=style, emoji=emoji, custom_id=f"channel.{channel.id}"))
        elif(type.value == "url"):
            view.add_item(discord.ui.Button(label=label, style=discord.ButtonStyle.url, url=value))
        
        await message.edit(view=view)
        embed.description = "```Added button```"
        await interaction.response.send_message(embed=embed)
    
    @button.command()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def clear(self, interaction: discord.Interaction, message: str):
        message = await interaction.channel.fetch_message(int(message))
        await message.edit(view=None)
        embed = self.embed.create_embed(interaction.user)
        embed.description = "```Cleared buttons```"
        await interaction.response.send_message(embed=embed)

    @commands.is_owner()
    @commands.guild_only()
    @commands.command()
    async def sync(self, ctx: commands.Context):
        self.tree.copy_global_to(guild=ctx.guild)
        fmt = await self.bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"Synced {len(fmt)} commands for guild")
    
    @commands.is_owner()
    @commands.command()
    async def globalsync(self, ctx: commands.Context):
        fmt = await self.bot.tree.sync(guild=None)
        await ctx.send(f"Synced {len(fmt)} commands globally")
    
    @commands.is_owner()
    @commands.command()
    async def clearsync(self, ctx: commands.Context):
        ctx.bot.tree.clear_commands(guild=None)
        await ctx.bot.tree.sync(guild=None)
        await ctx.send(f"Cleared global command tree")
    
    @commands.hybrid_command(description="Returns latency of bot")
    async def ping(self, ctx):
        ping1 = f"{str(round(self.bot.latency * 1000))} ms"
        embed = discord.Embed(title= "**Pong!**", description=f"**{ping1}**", color=0xafdafc)
        await ctx.send(embed=embed)
    
async def setup(bot):
    await bot.add_cog(Buttons(bot))