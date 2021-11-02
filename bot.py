import discord
from discord.ext import commands
import os
import logging

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)-19s | %(levelname)-8s | %(name)-16s | %(message)-s', "%d-%m-%Y %H:%M:%S")
ch.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(ch)

discordLogger = logging.getLogger('discord')
discordLogger.setLevel(logging.WARNING)

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.music"

class Main(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(f"{__cogname__}")
        self.logger.setLevel(logging.INFO)
        self.logger.info(f"Loaded {__cogname__}")

        os.makedirs(f"{os.getcwd()}/settings", exist_ok=True)
    
    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info(f"Logged in as {self.bot.user.name}")
        for cog in os.listdir(r"cogs"): # Loop through each file in your "cogs" directory.
            if cog.endswith(".py"):
                try:
                    cog = f"cogs.{cog.replace('.py', '')}"
                    self.bot.load_extension(cog) # Load the file as an extension.
                except Exception as e:
                    print(f"{cog} is failed to load:")
                    raise e

bot = commands.Bot(command_prefix=os.getenv("PREFIX"), intents=discord.Intents.all())

bot.add_cog(Main(bot))
bot.run(os.getenv("TOKEN"))