import discord
import asyncio
import aiohttp
import os

import youtube_dl
import re
import json

from discord.ext import commands

import logging
import random

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.music"
logger = logging.getLogger(__cogname__)

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Youtube:
    def __init__(self, session: aiohttp.ClientSession):
        self.key = os.getenv("YOUTUBE")
        apiYoutube = "https://www.googleapis.com/youtube/v3/"
        self.apiYoutubeSearch = apiYoutube + "search?key="+self.key+"&part=snippet&type=video&q={query}"
        self.apiYoutubeVideo = apiYoutube+"videos?key="+self.key+"&part=snippet,contentDetails,status,statistics&id={id}"
        self.apiYoutubeList = apiYoutube+"playlistItems?key="+self.key+"&part=snippet,contentDetails&maxResults=50&playlistId={id}"

        self.logger = logging.getLogger(self.__class__.__name__)

        self.session = session

    async def search_video(self, query):
        async with self.session.get(self.apiYoutubeSearch.format(query=query)) as resp:
            data = await resp.json()
            return data, resp.status

    async def get_video(self, video):
        async with self.session.get(self.apiYoutubeVideo.format(id=video)) as resp:
            data = await resp.json()
            return data, resp.status
    
    async def get_list(self, playlist):
        async with self.session.get(self.apiYoutubeList.format(id=playlist)) as resp:
            data = await resp.json()
            return data, resp.status
    
    async def validate_key(self):
        async with self.session.get(self.apiYoutubeVideo.format(id="YPN0qhSyWy8")) as resp:
            if resp.status != 200:
                self.logger.info(resp)
                response = await resp.json()
                message = response["error"]["message"]
                self.logger.warning(f"{resp.status}: {message}")
                return False
        return True

class Video:
    def __init__(self, user, url, title=None, description=None):
        self.user = user
        self.url = url
        self.title = title
        self.description = description
    def __str__(self):
        return self.url


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger

        self.session = aiohttp.ClientSession()
        self.yt = None
        loop = asyncio.get_event_loop()
        loop.create_task(self.load_yt())

        self._volume = {}
        
        self.currPlaying = {}
        self.soundTrack = {}

        self.embedColors = {121546822765248512:int("0x0066BB", 0), 168463608580276224:int("0x0066BB", 0), 103215649530077184:int("0x10DF19", 0)}

        self.exceptionNotConnected = "Currently not connected to a voice channel"
        self.exceptionNotPlaying = "There's nothing playing currently"
        self.exceptionAlreadyPlaying = "There's already something playing currently"
    
    async def load_yt(self):
        yt = Youtube(self.session)
        if(await yt.validate_key()):
            self.yt = yt
            self.logger.info("Youtube API Key validation passed")
            await self.read_playlist()
        else:
            self.logger.warning("Youtube API Key validation didn't pass, unloading cog")
            self.bot.unload_extension(f'cogs.{os.path.basename(__file__)}')
    
    def cog_unload(self):
        self.logger.info("Cog was unloaded")
        if not self.session.closed:
            self.logger.info("Stopping aiohttp session")
            fut = asyncio.ensure_future(self.session.close())
            yield from fut.__await__()
    
    @commands.command()
    async def add(self, ctx, arg):
        regex = re.search(r"^(?:https?:)?(?:\/\/)?(?:youtu\.be\/|(?:www\.|m\.)?youtube\.com\/(?:watch|v|embed)(?:\.php)?(?:\?.*v=|\/))([a-zA-Z0-9\_-]{7,15})(?:[\?&][a-zA-Z0-9\_-]+=[a-zA-Z0-9\_-]+)*$", arg)
        if regex == None:
            url = arg
        else:
            url = regex.group(1)
        video = await self.parse_video(ctx.author, url)
        embed = self.create_embed(ctx.author.id)
        embed.set_footer(text=f"Requested by: {ctx.author}", icon_url=ctx.author.avatar_url)
        if(video != None):
            self.soundTrack[ctx.guild.id].append(video)
            embed.description = f"**Added**:\n**[{video.title}](https://www.youtube.com/watch?v={video.url} '{video.url}')**"
        else:
            embed.title = f"Could not find video with {url}"
        await ctx.send(embed=embed)
        await self.write_playlist()
    
    @commands.command(aliases=["rem", "del"])
    async def remove(self, ctx, arg):
        embed = self.create_embed(ctx.author.id)

        index = int(arg)-1
        try:
            video = self.soundTrack[ctx.guild.id].pop(index)
            embed.set_author(name=f"{ctx.author}", icon_url=ctx.author.avatar_url)
            embed.description = f"**Removed**:\n**[{video.title}](https://www.youtube.com/watch?v={video.url} '{video.url}')**"
            #embed.set_footer(text=f"Requested by: {video.user}", icon_url=video.user.avatar_url)
        except IndexError:
            embed.description = f"Invalid index given"
        await ctx.send(embed=embed)
        await self.write_playlist()
    
    @commands.command(aliases=["p"])
    async def play(self, ctx):
        vc = ctx.voice_client
        if(vc.is_playing()):
            return await ctx.send(self.exceptionAlreadyPlaying)
        if(vc.is_paused()):
            return vc.resume()
        if(len(self.soundTrack[ctx.guild.id]) == 0):
            self.currPlaying[ctx.guild.id] = None
            await self.disconnect_safe(vc)
        
        self.currPlaying[ctx.guild.id] = self.soundTrack[ctx.guild.id].pop(0)
        player = await YTDLSource.from_url(self.currPlaying[ctx.guild.id].url, loop=self.bot.loop, stream=True)
        player.volume = self._volume[ctx.guild.id]

        vc.play(player, after=lambda e: self.finish(ctx, e))
        vc.source.volume = self._volume[ctx.guild.id]

        embed = self.create_embed(self.currPlaying[ctx.guild.id].user.id)
        if self.currPlaying[ctx.guild.id].title != None:
            embed.description = f"**Started playing:**\n**[{self.currPlaying[ctx.guild.id].title}](https://www.youtube.com/watch?v={self.currPlaying[ctx.guild.id].url} '{self.currPlaying[ctx.guild.id].url}')**"
        embed.set_footer(text=f"Requested by: {self.currPlaying[ctx.guild.id].user}", icon_url=self.currPlaying[ctx.guild.id].user.avatar_url)
        await ctx.send(embed=embed)
        await self.write_playlist()
    
    def finish(self, ctx, err):
        if err != None:
            vc = ctx.voice_client
            self.currPlaying[ctx.guild.id] = None
            #self.soundTrack[ctx.guild.id] = []
            fut = asyncio.run_coroutine_threadsafe(self.disconnect_safe(vc), self.bot.loop)
            try:
                fut.result()
            except:
                pass
        else:
            fut = asyncio.run_coroutine_threadsafe(ctx.invoke(self.bot.get_command("play")), self.bot.loop)
            try:
                fut.result()
            except:
                pass

    @commands.command()
    async def stop(self, ctx):
        vc = ctx.voice_client
        if vc == None:
            return
        self.currPlaying[ctx.guild.id] = None
        self.soundTrack[ctx.guild.id] = []
        vc.stop()

    @commands.command()
    async def pause(self, ctx):
        vc = ctx.voice_client
        if vc == None:
            return
        vc.pause()
    
    @commands.command()
    async def resume(self, ctx):
        vc = ctx.voice_client
        if vc == None:
            return
        vc.resume()

    @commands.command(aliases=["vol"])
    async def volume(self, ctx, volume):
        self._volume[ctx.guild.id] = float(volume) / 100
        vc = ctx.voice_client
        if(vc != None):
            if(vc.source != None):
                vc.source.volume = self._volume[ctx.guild.id]
        await ctx.send(f"Changed volume to {volume}%")
    
    @commands.command()
    async def skip(self, ctx):
        vc = ctx.voice_client
        if vc == None:
            return
        await ctx.send(f"Skipping {self.currPlaying[ctx.guild.id].title}")
        vc.stop()
    
    @commands.command(aliases=["now", "curr"])
    async def current(self, ctx):
        vc = ctx.voice_client
        if vc == None:
            return
        embed = self.create_embed()
        if vc.is_playing() or vc.is_paused():
            embed.color = self.embedColors.get(self.currPlaying[ctx.guild.id].user.id, int("0xFF0000", 0))
            if self.currPlaying[ctx.guild.id].title != None:
                embed.description = f"**Currently playing:**\n**[{self.currPlaying[ctx.guild.id].title}](https://www.youtube.com/watch?v={self.currPlaying[ctx.guild.id].url} '{self.currPlaying[ctx.guild.id].url}')**"
            embed.set_footer(text=f"Requested by: {self.currPlaying[ctx.guild.id].user}", icon_url=self.currPlaying[ctx.guild.id].user.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=["next"])
    async def queue(self, ctx):
        vc = ctx.voice_client
        embed = discord.Embed()
        embed.title = embed.Empty
        embed.url = embed.Empty
        songList = ["**Next songs:**"]
        if(len(self.soundTrack[ctx.guild.id]) > 0):
            for i in range(len(self.soundTrack[ctx.guild.id])):
                songList.append(f"[{i+1}/{len(self.soundTrack[ctx.guild.id])}] **[{self.soundTrack[ctx.guild.id][i].title}](https://www.youtube.com/watch?v={self.soundTrack[ctx.guild.id][i].url} '{self.soundTrack[ctx.guild.id][i].url}')**")
                if i == 4:
                    if(len(self.soundTrack[ctx.guild.id])-5 > 0):
                        songList.append(f"And {len(self.soundTrack[ctx.guild.id])-5} more")
                    break
        else:
            songList.append("Empty")
        embed.description = "\n".join(songList)

        if vc == None:
            embed.color = self.embedColors.get(ctx.author.id, int("0xFF0000", 0))
        elif vc.is_playing() or vc.is_paused():
            embed.color = self.embedColors.get(self.currPlaying[ctx.guild.id].user.id, int("0xFF0000", 0))
            if self.currPlaying[ctx.guild.id].title != None:
                embed.add_field(name="Currently playing:", value=f"**[{self.currPlaying[ctx.guild.id].title}](https://www.youtube.com/watch?v={self.currPlaying[ctx.guild.id].url} '{self.currPlaying[ctx.guild.id].url}')**")
                embed.set_footer(text=f"Requested by: {self.currPlaying[ctx.guild.id].user}", icon_url=self.currPlaying[ctx.guild.id].user.avatar_url)

        await ctx.send(embed=embed)

    @commands.command()
    async def connect(self, ctx):
        await self.ensure_voice(ctx)
    
    @commands.command()
    async def disconnect(self, ctx):
        await self.disconnect_safe(ctx.voice_client)

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author's not connected to a voice channel.")
        await self.ensure_volume(ctx)
        await ctx.guild.change_voice_state(channel=ctx.voice_client.channel, self_mute=False, self_deaf=True)
    
    @add.before_invoke
    @queue.before_invoke
    @current.before_invoke
    async def ensure_playlist(self, ctx):
        if ctx.guild.id not in self.soundTrack.keys():
            self.soundTrack[ctx.guild.id] = []
        elif not isinstance(self.soundTrack[ctx.guild.id], list):
            self.soundTrack[ctx.guild.id] = []
    
    @volume.before_invoke
    async def ensure_volume(self, ctx):
        if ctx.guild.id not in self._volume.keys():
            self._volume[ctx.guild.id] = 100.0
    
    async def disconnect_safe(self, vc):
        if(not vc.is_connected()):
            return
        if(vc.is_playing() or vc.is_paused()):
            vc.stop()
        await vc.disconnect()

    async def parse_video(self, user, url):
        if(self.yt != None):
            data, status = await self.yt.get_video(url)
            if(status != 200):
                return None
            if(len(data["items"]) == 0):
                return None
            video = data["items"][0]
            return Video(user, video["id"], video["snippet"]["title"], video["snippet"]["description"])
    
    def create_embed(self, id=0):
        embed = discord.Embed()
        embed.color = self.embedColors.get(id, int("0xFF0000", 0))
        embed.title = embed.Empty
        embed.url = embed.Empty
        return embed
    
    async def read_playlist(self):
        if not os.path.isfile(f"{os.getcwd()}/settings/music.json"):
            return
        try:
            with open(f"{os.getcwd()}/settings/music.json", "r") as file:
                songs = json.load(file)
            for key in songs.keys():
                self.soundTrack[int(key)] = []
                for song in songs[key]:
                    user = self.bot.get_user(song[0])
                    video = await self.parse_video(user, song[1])
                    self.soundTrack[int(key)].append(video)
            self.logger.info(f"Loaded songs from {len(self.soundTrack.keys())} guilds")
        except json.decoder.JSONDecodeError:
            pass

    async def write_playlist(self):
        songs = {}
        for key in self.soundTrack.keys():
            songs[key] = []
            for song in self.soundTrack[key]:
                songs[key].append((song.user.id, song.url))
        json_object = json.dumps(songs, indent=4)
        with open(f"{os.getcwd()}/settings/music.json", "w") as file:
            file.write(json_object)

def setup(bot):
    bot.add_cog(Music(bot))