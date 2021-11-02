import logging
import aiohttp
from urllib import parse
import traceback
import discord
import asyncio

from discord.ext import commands

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.derpibooru"
logger = logging.getLogger(__cogname__)

class Derpibooru(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
    
    def cog_unload(self):
        self.logger.info("Cog was unloaded")
        if not self.session.closed:
            self.logger.info("Stopping aiohttp session")
            fut = asyncio.ensure_future(self.session.close())
            yield from fut.__await__()

    # Commands
    @commands.command(aliases=["derpi", "derpibooru"])
    @commands.guild_only()
    async def pony(self, ctx, *text):
        if(ctx.message.channel.id != 551482347581603861 and ctx.message.channel.id != 608013362365857898):
            return
        """ Returns image from derpibooru based off given command """
        embedLink = ""
        embedTitle = ""
        imageId = ""
        output = None
        ratingColor = "0066BB"
        search = "https://derpibooru.org/api/v1/json/search/images?sf=random&per_page=1&q="
        tags = []
        addtags = ["safe", "score.gte:100"]
        tagSearch = ""

        for x in list(text):
            tags.append(x.replace("[","").replace("]","").replace('"','').replace(" ","").replace(",","").replace("[",""))
        for tag in tags:
            if(tag[:12] == "questionable"):
                tags.remove(tag)
            if(tag[:10] == "suggestive"):
                tags.remove(tag)
            if(tag[:8] == "explicit"):
                tags.remove(tag)
            if(tag[:4] == "safe"):
                addtags.remove("safe")
            if(tag[:5] == "score"):
                addtags.remove("score.gte:100")
        tags += addtags
        tagSearch = "{} ".format(",".join(tags).strip())
        search += parse.quote_plus(tagSearch)
        try:
            async with aiohttp.ClientSession(loop=ctx.bot.loop) as session:
                async with session.get(search, headers={"User-Agent": "Booru-Bot"}) as r:
                    website = await r.json()
            if website["total"] > 0:
                website = website["images"][0]
                imageId = website["id"]
                imageURL = website["representations"]["full"]
            else:
                return await ctx.send(content="Your search terms gave no results.")
        except Exception as e:
            traceback.print_exc()
            return await ctx.send(content="Error! Contact bot owner.")

        embedTitle = "Derpibooru Image #{}".format(imageId)

        # Sets the URL to be linked
        embedLink = "https://derpibooru.org/{}".format(imageId)

        # Initialize verbose embed
        output = discord.Embed(title=embedTitle, url=embedLink, colour=discord.Colour(value=int(ratingColor, 16)))
        output.set_image(url=imageURL)

        await ctx.send(embed=output)
    
def setup(bot):
    bot.add_cog(Derpibooru(bot))