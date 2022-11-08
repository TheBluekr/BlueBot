import logging
import discord
import typing
import json
import requests
from io import BytesIO
import imghdr

from discord.ext import commands

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.personalroles"
logger = logging.getLogger(__cogname__)

class PersonalRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        self.logger.info(f"Loaded cog {__cogname__}")
        self.cache = {}
        try:
            with open("./settings/personalroles.json", "r") as fp:
                self.cache = json.load(fp)
        except:
            pass
    
    async def write(self):
        with open("./settings/personalroles.json", "w") as fp:
            json.dump(self.cache, fp, sort_keys=True, indent=4)
    
    def is_guild_owner():
        async def predicate(ctx):
            return ctx.author == ctx.guild.owner
        return commands.check(predicate)
    
    @commands.group(pass_context=True)
    async def pr(self, ctx):
        pass

    @pr.error
    async def pr_error(self, ctx, error):
        if(isinstance(error, commands.CheckFailure)):
            return

    @is_guild_owner()
    @pr.command()
    async def add(self, ctx, member: discord.Member, role: discord.Role):
        if(self.cache.get(str(member.id), None) != None):
            await ctx.send(f"{member} already has assigned role {role}")
            return
        self.cache[str(member.id)] = str(role.id)
        await self.write()
        await ctx.send(f"Succesfully added {member} with role {role}")
    
    @add.error
    async def add_error(self, ctx, error):
        if(isinstance(error, commands.RoleNotFound)):
            await ctx.send(str(error))
    
    @is_guild_owner()
    @pr.command()
    async def remove(self, ctx, member: discord.Member, role: discord.Role):
        self.cache.pop(member.id, None)
        await self.write()
        await ctx.send(f"Succesfully removed {member} with role {role}")
    
    @is_guild_owner()
    @pr.command()
    async def list(self, ctx):
        message = "```"
        for key, value in self.cache.items():
            message += f"{ctx.guild.get_member(int(key))} - {ctx.guild.get_role(int(value))}\n"
        message += "```"
        await ctx.send(message)

    @pr.command()
    async def name(self, ctx, name: str):
        role = ctx.author.get_role(int(self.cache.get(str(ctx.author.id), 0)))
        if(role == None):
            return
        await role.edit(name=name)
    
    @pr.command()
    async def color(self, ctx, color: discord.Colour):
        role = ctx.author.get_role(int(self.cache.get(str(ctx.author.id), 0)))
        if(role == None):
            return
        await role.edit(color=color)
    
    @pr.command()
    async def icon(self, ctx, url=None):
        role = ctx.author.get_role(int(self.cache.get(str(ctx.author.id), 0)))
        if(role == None):
            return
        if(len(ctx.message.attachments) == 0 and url == None):
            return await role.edit(display_icon=None)
        bytes = None
        if(url != None):
            response = requests.get(url)
            if(response.status_code != 200):
                return await ctx.send(f"URL return error code {response.status_code}")
            bytes = BytesIO(response.content)
            if(imghdr.what(bytes) == None):
                return await ctx.send(f"Invalid image format provided in URL")
        else:             
            attachment = ctx.message.attachments[0]
            bytes = BytesIO(await attachment.read())
        if(bytes.getbuffer().nbytes > 1024*256): # 262144
            return await ctx.send("Attachment is over the 256kb file size limit")
        await role.edit(display_icon=bytes)
    
    @color.error
    async def color_error(self, ctx, error):
        if(isinstance(error, commands.BadColorArgument)):
            await ctx.send("Invalid color format given")

async def setup(bot):
    await bot.add_cog(PersonalRoles(bot))