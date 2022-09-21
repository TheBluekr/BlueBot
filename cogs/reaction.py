import logging
import discord

from discord.ext import commands

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.reactionrole"
logger = logging.getLogger(__cogname__)

class ReactionRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        self.logger.info(f"Loaded cog {__cogname__}")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if(reaction.message.id == 951497250968850432):
            if(type(reaction.emoji) == str):
                if(reaction.emoji == "✅"):
                    role = reaction.message.guild.get_role(438985566911070209)
                    await user.add_roles(role)
                if(reaction.emoji == "🔞"):
                    role = reaction.message.guild.get_role(864831873505820693)
                    await user.add_roles(role)
    
    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if(reaction.message.id == 951497250968850432):
            if(type(reaction.emoji) == str):
                if(reaction.emoji == "✅"):
                    role = reaction.message.guild.get_role(438985566911070209)
                    await user.remove_roles(role)
                if(reaction.emoji == "🔞"):
                    role = reaction.message.guild.get_role(864831873505820693)
                    await user.remove_roles(role)

    
async def setup(bot):
    await bot.add_cog(ReactionRole(bot))