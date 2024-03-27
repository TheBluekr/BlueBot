import logging
import discord
import datetime
import copy

from discord.ext import commands, tasks

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.recentping"
logger = logging.getLogger(__cogname__)

class RecentPing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        self.logger.info(f"Loaded cog {__cogname__}")
        self.embed = self.bot.embed
        self.guildUserHistory = {}
        self.guildRole = {}

    @tasks.loop(count=1)
    async def async_init(self):
        await self.bot.wait_until_ready()
        guild: discord.Guild
        for guild in self.bot.guilds:
            for role in guild.roles:
                if role.name == "recent":
                    self.guildRole[guild.id] = role.id
                    break
            if(self.guildRole.get(guild.id) == None):
                self.guildRole[guild.id] = 0
        self.check_recent.start()

    @tasks.loop(seconds=10)
    async def check_recent(self):
        buffer = copy.deepcopy(self.guildUserHistory)
        memberTimestamp = dict()
        for guildId, memberTimestamp in buffer.items():
            for memberId, timestamp in memberTimestamp.items():
                guild: discord.Guild = self.bot.get_guild(guildId)
                now = datetime.datetime.now()
                if(timestamp < now):
                    member: discord.Member = guild.get_member(memberId)
                    role: discord.Role = guild.get_role(self.guildRole.get(guildId))
                    if(member and role):
                        await member.remove_roles(role)
                        self.guildUserHistory[guildId].pop(memberId)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        author = message.author
        guild = message.guild
        role = guild.get_role(self.guildRole[guild.id])
        if(self.guildUserHistory.get(guild.id) == None):
            self.guildUserHistory[guild.id] = dict()
        self.guildUserHistory[guild.id][author.id] = datetime.datetime.now()+datetime.timedelta(minutes=5)
        if(author.get_role(self.guildRole[guild.id]) == None and role != None):
            await author.add_roles(role)
    
    async def cog_load(self):
        self.async_init.start()
    
    async def cog_unload(self):
        for guildId, memberTimestamp in self.guildUserHistory.items():
            for memberId, timestamp in memberTimestamp.items():
                guild: discord.Guild = self.bot.get_guild(guildId)
                member: discord.Member = guild.get_member(memberId)
                role: discord.Role = guild.get_role(self.guildRole.get(guildId))
                if(member and role):
                    await member.remove_roles(role)

async def setup(bot):
    await bot.add_cog(RecentPing(bot))