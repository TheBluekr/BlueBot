import discord
from discord.ext import commands
import os
import logging
from core import Database, EmbedColor, Git

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)-19s | %(levelname)-8s | %(name)-26s | %(message)-s', "%d-%m-%Y %H:%M:%S")
ch.setFormatter(formatter)

fh = logging.FileHandler("logs.txt", mode="w")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(ch)
logger.addHandler(fh)

discordLogger = logging.getLogger('discord')
discordLogger.setLevel(logging.WARNING)

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.main"

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=os.getenv("PREFIX"), intents=discord.Intents.all())
        self.logger = logging.getLogger(f"{__cogname__}")
        self.logger.setLevel(logging.INFO)
        self.logger.info(f"Loaded {__cogname__}")

        self.db = Database()

        self.embed = EmbedColor(self)
        
        self.git = Git(self)

        os.makedirs(f"{os.getcwd()}/settings", exist_ok=True)
    
    async def setup_hook(self):
        for cog in os.listdir(r"cogs"):
            if cog.endswith(".py"):
                try:
                    cog = f"cogs.{cog.replace('.py', '')}"
                    await self.load_extension(cog)
                except Exception as e:
                    self.logger.error(f"{cog} is failed to load:")
                    raise e
        
        self.logger.info("Finished loading all cogs")
        return await super().setup_hook()

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info(f"Logged in as {self.user.name}")
        #fmt = await self.tree.sync()
        #self.logger.info(f"Synced {len(fmt)} commands")
    
    @commands.Cog.listener()
    async def on_disconnect(self):
        self.db.close()
    
    @commands.command()
    async def restart(self, ctx: commands.Context):
        await self.close()

bot = Bot()
bot.run(os.getenv("TOKEN"), log_handler=None)

#asyncio.run(boot())