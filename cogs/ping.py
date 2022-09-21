import logging
import discord
import re

from discord.ext import commands, tasks

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.pinghistory"
logger = logging.getLogger(__cogname__)

class PingMessage:
    def __init__(self, message: discord.Message):
        self.logger = logger
        self.id = message.id
        self.author = message.author.id
        limit = 150

        if(len(message.content) > limit):
            p = re.compile("(<@!*&*[0-9]+>)|(\S[a-zA-Z0-9]*)|([ ]*)")
            for m in p.finditer(message.content):
                if(m.end() > limit):
                    self.content = f"{message.content[:m.start()]} <snip>"
                    break
        else:
            self.content = message.content
        self.url = message.jump_url

class PingHistory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        self.logger.info(f"Loaded cog {__cogname__}")
        self.embedColors = {121546822765248512:int("0066FF", 16)}
        self.userHistory = {}

        if(self.bot.is_ready()):
            self.setup_users()

    @commands.Cog.listener()
    async def on_ready(self):
        self.setup_users()

    @commands.guild_only()
    @commands.command()
    async def pings(self, ctx, member: discord.Member=None):
        if(member == None):
            member = ctx.author
        embed = self.create_embed(member.id)
        pings = self.userHistory[member.id][ctx.message.guild.id]
        for ping in pings:
            embed.add_field(name=f"{self.bot.get_user(ping.author)}", value=f"[Jump to message]({ping.url})\n{ping.content}", inline=True)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if(message.author.id == self.bot.user.id):
            return
        if(self.checkcommand(message)):
            return
        ping = PingMessage(message)
        if(message.mention_everyone):
            for member in message.guild.members:
                self.userHistory[member.id][message.guild.id].insert(0, ping)
                del self.userHistory[member.id][message.guild.id][3:]
        elif(len(message.role_mentions) > 0):
            for role in message.role_mentions:
                for member in role.members:
                    if(len(self.userHistory[member.id][message.guild.id]) > 0):
                        if(self.userHistory[member.id][message.guild.id][0].id == ping.id):
                            continue
                    self.userHistory[member.id][message.guild.id].insert(0, ping)
                    del self.userHistory[member.id][message.guild.id][3:]
        elif(len(message.mentions) > 0):
            for member in message.mentions:
                self.userHistory[member.id][message.guild.id].insert(0, ping)
                del self.userHistory[member.id][message.guild.id][3:]
    
    def setup_users(self):
        for guild in self.bot.guilds:
            for member in guild.members:
                if(member.id not in self.userHistory.keys()):
                    self.userHistory[member.id] = {}
                if(guild.id not in self.userHistory[member.id].keys()):
                    self.userHistory[member.id][guild.id] = []
    
    def create_embed(self, id=0):
        embed = discord.Embed()
        embed.color = self.embedColors.get(id, int("0xFFFFFF", 16))
        embed.title = f"History of pings for {self.bot.get_user(id)}"
        embed.url = None
        return embed
    
    def checkcommand(self, message: discord.Message):
        message_prefix = message.content[:len(self.bot.command_prefix)]
        if(message_prefix != self.bot.command_prefix):
            return False
        message_suffix = message.content[len(self.bot.command_prefix):].split()
        commands = [c.name for c in self.bot.commands]
        if(message_suffix[0] not in commands):
            return False
        return True

async def setup(bot):
    await bot.add_cog(PingHistory(bot))