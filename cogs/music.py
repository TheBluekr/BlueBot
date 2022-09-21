import discord
import asyncio
import aiohttp
import os
from discord.errors import InvalidData

import youtube_dl
import re
import json
import datetime

from discord.ext import commands, tasks

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
    'logger': logger,
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

class InvalidKey(Exception):
    pass

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
    def __init__(self, user, url, title=None, description=None, duration=None):
        self.user = user
        self.url = url
        self.title = title
        self.description = description
        #search = re.search(r"^P([0-9]{0,2}D)?T([0-9]{0,2}H)?([0-9]{0,2}M)?([0-9]{0,2})(?:S)$", duration)
        # Really hacky method of finding days, h:m:s when it doesn't always format like that... ISO 8601 sucks
        #duration = 0
        #if search.group(1) != None:
        #    duration += int(search.group(1).strip("D"))*24*60*60
        #if search.group(2) != None:
        #    duration += int(search.group(2).strip("H"))*60*60
        #if search.group(3) != None:
        #    duration += int(search.group(3).strip("M"))*60
        #if search.group(4) != None:
        #    duration += int(search.group(4).strip("S"))
        self.duration = duration
    def __str__(self):
        return self.url


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger

        self.session = aiohttp.ClientSession()
        self.yt = None
        self.async_init.start()

        self._volume = {}
        
        self.currPlaying = {}
        self.soundTrack = {}
        self.endTime = {}
        self.attempts = {}
        self.stopSong = {}

        self.playlistFile = f"{os.getcwd()}/settings/music.playlist.json"
        self.embedFile = f"{os.getcwd()}/settings/music.embed.json"

        self.embedColors = {}

        self.exceptionNotConnected = "Currently not connected to a voice channel"
        self.exceptionNotPlaying = "There's nothing playing currently"
        self.exceptionAlreadyPlaying = "There's already something playing currently"
    
    def cog_unload(self):
        self.logger.info("Cog was unloaded")
        if not self.session.closed:
            self.logger.info("Stopping aiohttp session")
            fut = asyncio.ensure_future(self.session.close())
            yield from fut.__await__()
    
    @tasks.loop(count=1)
    async def async_init(self):
        await self.read_playlist()
        await self.read_embed_colors()

    @async_init.before_loop
    async def before_yt(self):
        self.yt = Youtube(self.session)
        if(await self.yt.validate_key()):
            self.logger.info("Youtube API Key validation passed")
        else:
            raise InvalidKey("Youtube API Key validation didn't pass")
    
    @commands.command()
    async def add(self, ctx, arg):
        regex = re.search(r"^(?:https?:)?(?:\/\/)?(?:youtu\.be\/|(?:www\.|m\.)?youtube\.com\/(?:watch|v|embed)(?:\.php)?(?:\?.*v=|\/))([a-zA-Z0-9\_-]{7,15})(?:[\?&][a-zA-Z0-9\_-]+=[a-zA-Z0-9\_-]+)*$", arg)
        if regex == None:
            url = arg
        else:
            url = regex.group(1)
        video = await self.parse_video(ctx.author, url)
        embed = self.create_embed(ctx.author.id)
        embed.set_footer(text=f"Requested by: {ctx.author}", icon_url=ctx.author.display_avatar.url)
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
            embed.set_author(name=f"{ctx.author}", icon_url=ctx.author.display_avatar.url)
            embed.description = f"**Removed**:\n**[{video.title}](https://www.youtube.com/watch?v={video.url} '{video.url}')**"
            #embed.set_footer(text=f"Requested by: {video.user}", icon_url=video.user.display_avatar.url)
        except IndexError:
            embed.description = f"Invalid index given"
        await ctx.send(embed=embed)
        await self.write_playlist()
    
    @commands.command(aliases=["p"])
    async def play(self, ctx, url: str=None):
        if(url != None):
            await self.add(ctx, url)
        vc = ctx.voice_client
        if(vc.is_playing() and url == None):
            return await ctx.send(self.exceptionAlreadyPlaying)
        if(vc.is_paused()):
            return vc.resume()
        self.attempts[ctx.guild.id] = 0
        await self.play_song(ctx)
    
    async def play_song(self, ctx):
        vc = ctx.voice_client
        if(len(self.soundTrack[ctx.guild.id]) == 0 and self.currPlaying[ctx.guild.id] == None):
            await self.disconnect_safe(vc)
        
        self.currPlaying[ctx.guild.id] = self.soundTrack[ctx.guild.id].pop(0)
        #self.endTime[ctx.guild.id] = datetime.datetime.now() + datetime.timedelta(seconds=self.currPlaying[ctx.guild.id].duration)
        self.endTime[ctx.guild.id] = datetime.datetime.now() + datetime.timedelta(seconds=2)

        player = await YTDLSource.from_url(self.currPlaying[ctx.guild.id].url, loop=self.bot.loop, stream=True)
        player.volume = self._volume[ctx.guild.id]

        vc.play(player, after=lambda e: self.finish(ctx, e))
        vc.source.volume = self._volume[ctx.guild.id]

        embed = self.create_embed(self.currPlaying[ctx.guild.id].user.id)
        if self.currPlaying[ctx.guild.id].title != None:
            embed.description = f"**Started playing:**\n**[{self.currPlaying[ctx.guild.id].title}](https://www.youtube.com/watch?v={self.currPlaying[ctx.guild.id].url} '{self.currPlaying[ctx.guild.id].url}')**"
        embed.set_footer(text=f"Requested by: {self.currPlaying[ctx.guild.id].user}", icon_url=self.currPlaying[ctx.guild.id].user.display_avatar.url)
        await ctx.send(embed=embed)
        await self.write_playlist()
    
    def finish(self, ctx, err):
        if(self.endTime[ctx.guild.id] > datetime.datetime.now() and err != None and not self.stopSong.get(ctx.guild.id, False)):
            # Potential bug fix, replay the song if it ended prematurely...
            self.soundTrack[ctx.guild.id].insert(0, self.currPlaying[ctx.guild.id])
            self.attempts[ctx.guild.id] += 1
            self.logger.warning("Song ended prematurely for unknown reasons, attempting to replay")
        self.currPlaying[ctx.guild.id] = None
        if err != None and self.attempts[ctx.guild.id] >= 3:
            self.logger.error(err)
            vc = ctx.voice_client
            #self.soundTrack[ctx.guild.id] = []
            fut = asyncio.run_coroutine_threadsafe(self.disconnect_safe(vc), self.bot.loop)
            try:
                fut.result()
            except:
                pass
            fut = asyncio.run_coroutine_threadsafe(ctx.send(f"Error occured:\n{err}"), self.bot.loop)
            try:
                fut.result()
            except:
                pass
        else:
            self.attempts[ctx.guild.id] = 0
            fut = asyncio.run_coroutine_threadsafe(self.play_song(ctx), self.bot.loop)
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
        self.stopSong[ctx.guild.id] = True
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
        self.currPlaying[ctx.guild.id] = None
        self.stopSong[ctx.guild.id] = True
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
            embed.set_footer(text=f"Requested by: {self.currPlaying[ctx.guild.id].user}", icon_url=self.currPlaying[ctx.guild.id].user.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(aliases=["next"])
    async def queue(self, ctx):
        vc = ctx.voice_client
        embed = self.create_embed()
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
                embed.set_footer(text=f"Requested by: {self.currPlaying[ctx.guild.id].user}", icon_url=self.currPlaying[ctx.guild.id].user.display_avatar.url)

        await ctx.send(embed=embed)

    @commands.command()
    async def connect(self, ctx):
        await self.ensure_voice(ctx)
    
    @commands.command()
    async def disconnect(self, ctx):
        await self.disconnect_safe(ctx.voice_client)
    
    @commands.is_owner()
    @commands.command()
    async def rembed(self, ctx):
        await self.read_embed_colors()
        embed = self.create_embed(ctx.author.id)
        embed.description = f"Reloaded embed color list with {len(self.embedColors)} colors"
        await ctx.send(embed=embed)

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
            return Video(user, video["id"], video["snippet"]["title"], video["snippet"]["description"], video["contentDetails"]["duration"])
    
    def create_embed(self, id=0):
        embed = discord.Embed()
        embed.color = self.embedColors.get(id, int("0xFF0000", 0))
        embed.title = None
        embed.url = None
        return embed
    
    async def read_embed_colors(self):
        if not os.path.isfile(self.embedFile):
            return
        try:
            with open(self.embedFile, "r") as file:
                embedColors = json.load(file)
            for key in embedColors.keys():
                self.embedColors[int(key)] = int(embedColors[key], 0)
            self.logger.info(f"Loaded {len(self.embedColors)} embed colors for users")
        except json.decoder.JSONDecodeError:
            pass
    
    async def read_playlist(self):
        if not os.path.isfile(self.playlistFile):
            return
        try:
            songcount = 0
            with open(self.playlistFile, "r") as file:
                songs = json.load(file)
            for key in songs.keys():
                self.soundTrack[int(key)] = []
                for song in songs[key]:
                    user = self.bot.get_user(song[0])
                    video = await self.parse_video(user, song[1])
                    self.soundTrack[int(key)].append(video)
                self.logger.info(f"Loaded {len(self.soundTrack[int(key)])} songs for guild {self.bot.get_guild(int(key))}")
        except json.decoder.JSONDecodeError:
            pass

    async def write_playlist(self):
        songs = {}
        for key in self.soundTrack.keys():
            songs[key] = []
            for song in self.soundTrack[key]:
                songs[key].append((song.user.id, song.url))
        json_object = json.dumps(songs, indent=4)
        with open(self.playlistFile, "w") as file:
            file.write(json_object)

async def setup(bot):
    await bot.add_cog(Music(bot))