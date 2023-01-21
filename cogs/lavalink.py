import discord
import asyncio
import os
import json

from discord.ext import commands
from discord import app_commands
import typing

import logging

import wavelink
import sponsorblock

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.lavalink"
logger = logging.getLogger(__cogname__)

waveLogger = logging.getLogger('wavelink')
waveLogger.setLevel(logging.WARNING)

class Track(wavelink.Track):
    __slots__ = ("requester", )

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.requester = kwargs.get("requester")
        self.sb = kwargs.get("sponsorblock")
        self.loop = kwargs.get("loop")

class Lavalink(commands.Cog):
    """Music cog to hold Wavelink related commands and listeners."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.bot.loop.create_task(self.post_init())

        self.embedColors = {}

        self.wavequeue = {}
        self.volume = {}
        self.sbClient = sponsorblock.Client()

        self.logger = logger

    async def post_init(self):
        await self.connect_nodes()
        await self.embed_colors()

    async def connect_nodes(self):
        """Connect to our Lavalink nodes."""
        await self.bot.wait_until_ready()

        await wavelink.NodePool.create_node(bot=self.bot, host='lavalink', port=8080, password='youshallnotpass')
    
    async def embed_colors(self):
        if not os.path.isfile(f"{os.getcwd()}/settings/music.embed.json"):
            return
        try:
            with open(f"{os.getcwd()}/settings/music.embed.json", "r") as file:
                embedColors = json.load(file)
            for key in embedColors.keys():
                self.embedColors[int(key)] = int(embedColors[key], 0)
            self.logger.info(f"Loaded {len(self.embedColors)} embed colors for users")
        except json.decoder.JSONDecodeError:
            pass
    
    async def get_player(self, guild):
        node = await self.get_node()
        return node.get_player(guild)
    
    @commands.Cog.listener()
    async def on_unloaded_extension(self, ext):
        node = wavelink.NodePool.get_node()
        await node.disconnect()

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        """Event fired when a node has finished connecting."""
        self.logger.info(f'Node: <{node.identifier}> is ready!')
    
    @commands.Cog.listener()
    async def on_wavelink_track_start(self, player, track):
        curr = self.wavequeue[player.guild].get()
        self.wavequeue[player.guild].put_at_front(curr)
        if(curr.identifier != track.identifier):
            await player.channel.send("Mismatch occured between expected and playing track, this is not intended.\nPlease contact the bot author if this occured.")
            await player.stop()
            return
        self.logger.info(f"Started playing: {curr.title} ({curr.identifier})")
        await player.set_volume(self.volume[player.guild])

        embed = discord.Embed(description=f"**Started playing**:\n**[{track.title}](https://www.youtube.com/watch?v={track.identifier} '{track.identifier}')**")
        if(curr.loop):
            embed.description += " (looped)"
        embed.set_footer(text=f"Requested by: {curr.requester}", icon_url=curr.requester.avatar.url)
        embed.color = self.embedColors.get(curr.requester.id, curr.requester.color)
        
        await player.channel.send(embed=embed)

        try:
            segments = self.sbClient.get_skip_segments(curr.identifier)
            segments.sort(key=lambda x: x.start)

            skips = self.process_sponsorblock(segments)

            # Prevent our player from lagging out the start
            if(curr.sb):
                await player.pause()
                currPos = 0
                if(len(skips) > 0):
                    if(currPos >= skips[0][0]):
                        self.logger.info(f"Skipping segment {skips[0][0]}-{skips[0][1]} at start")
                        await player.seek(skips[0][1]*1000)
                        del skips[0]
                await player.resume()
                while(len(skips) > 0):
                    currPos = player.position
                    if(skips[0][0] < currPos < skips[0][1]):
                        self.logger.info(f"Skipping segment {skips[0][0]}-{skips[0][1]}")
                        await player.seek(skips[0][1]*1000)
                        del skips[0]
                    elif(skips[0][1] < currPos):
                        self.logger.info(f"Went past segment {skips[0][0]}-{skips[0][1]}, removing")
                        del skips[0]
                    await asyncio.sleep(0.5)
        except sponsorblock.errors.NotFoundException:
            pass

    @commands.Cog.listener('on_wavelink_track_end')
    @commands.Cog.listener('on_wavelink_track_exception')
    @commands.Cog.listener('on_wavelink_track_stuck')
    async def on_player_stop(self, player: wavelink.Player, track, reason):
        previoustrack = self.wavequeue[player.guild].get()
        self.logger.info(f"Finished playing {previoustrack.title}")
        if(previoustrack.loop):
            self.wavequeue[player.guild].put_at_front(previoustrack)
        if(self.wavequeue[player.guild].count > 0):
            nexttrack = self.wavequeue[player.guild].get()
            self.wavequeue[player.guild].put_at_front(nexttrack)
            player.play(nexttrack)
        else:
            await player.disconnect()

    @commands.guild_only()
    @app_commands.describe(search="Url of youtube video")
    @commands.hybrid_command(description="Adds a track to play into the queue")
    async def add(self, ctx: commands.Context, url: str):
        #search: typing.Union[wavelink.YouTubeTrack, wavelink.YouTubeMusicTrack, wavelink.SoundCloudTrack, wavelink.YouTubePlaylist]
        search = await wavelink.NodePool.get_node().get_tracks(wavelink.YouTubeTrack, url)
        if(not search):
            embed = discord.Embed(description=f"Could not find track")
            embed.color = self.embedColors.get(ctx.author.id, ctx.author.color)
            await ctx.channel.send(embed=embed)
        else:
            track = Track(search[0].id, search[0].info, requester=ctx.author, sponsorblock=False if type(search) == wavelink.SoundCloudTrack else True, loop=False)
            self.wavequeue[ctx.guild].put(track)
            embed = discord.Embed(description=f"**Added**:\n**[{track.title}](https://www.youtube.com/watch?v={track.identifier} '{track.identifier}')**")
            embed.set_footer(text=f"Requested by: {ctx.author}", icon_url=ctx.author.avatar.url)
            embed.color = self.embedColors.get(ctx.author.id, ctx.author.color)
            await ctx.channel.send(embed=embed)
        
        #if(type(search) != wavelink.YouTubePlaylist):
            #track = Track(search.id, search.info, requester=ctx.author, sponsorblock=False if type(search) == wavelink.SoundCloudTrack else True, loop=False)
            #self.wavequeue[ctx.guild].put(track)
            #embed = discord.Embed(description=f"**Added**:\n**[{track.title}](https://www.youtube.com/watch?v={track.identifier} '{track.identifier}')**")
            #embed.set_footer(text=f"Requested by: {ctx.author}", icon_url=ctx.author.avatar.url)
            #embed.color = self.embedColors.get(ctx.author.id, ctx.author.color)
            #await ctx.channel.send(embed=embed)
        #elif(type(search) == wavelink.YouTubePlaylist):
            #for yttrack in search.tracks:
                #track = Track(yttrack.id, yttrack.info, requester=ctx.author, sponsorblock=True, loop=False)
                #self.wavequeue[ctx.guild].put(track)
            #embed = discord.Embed(description=f"**Added playlist**:\n**{search.name} ({len(search.tracks)} songs)**")
            #embed.set_footer(text=f"Requested by: {ctx.author}", icon_url=ctx.author.avatar.url)
            #embed.color = self.embedColors.get(ctx.author.id, ctx.author.color)
            #await ctx.channel.send(embed=embed)

    @commands.guild_only()
    #@app_commands.describe(search="Optional: Url of youtube video/playlist")
    #@commands.hybrid_command(description="Starts playing the current soundtrack")
    @commands.command()
    async def play(self, ctx: commands.Context, search: typing.Union[wavelink.YouTubeTrack, wavelink.YouTubeMusicTrack, wavelink.SoundCloudTrack]):
        """Play a song with the given search query. (Also accepts a song after invoke to add to the queue)
        """
        if(not ctx.voice_client):
            vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = ctx.voice_client
        if(search != None):
            track = Track(search.id, search.info, requester=ctx.author, sponsorblock=True, loop=False)
            self.wavequeue[ctx.guild].put(track)

            embed = discord.Embed(description=f"**Added**:\n**[{track.title}](https://www.youtube.com/watch?v={track.identifier} '{track.identifier}')**")
            embed.set_footer(text=f"Requested by: {track.requester}", icon_url=track.requester.avatar.url)
            embed.color = self.embedColors.get(track.requester.id, track.requester.color)
            await vc.channel.send(embed=embed)
            if(vc.is_paused()):
                await vc.resume()
            if(vc.is_playing()):
                pass
            else:
                await vc.play(track)
        else:
            if(vc.is_paused()):
                await vc.resume()
            elif(not vc.is_playing()):
                track = self.wavequeue[ctx.guild].get()
                self.wavequeue[ctx.guild].put_at_front(track)
                vc.play(next)
    
    @commands.guild_only()
    @commands.hybrid_command(description="Pause the current player")
    async def pause(self, ctx: commands.Context):
        """Pauses the music player.
        """
        if not ctx.voice_client:
            return
        vc: wavelink.Player = ctx.voice_client
        if(vc.source == None):
            return
        if(vc.is_playing()):
            embed = discord.Embed(description=f"Paused **[{vc.track.title}](https://www.youtube.com/watch?v={vc.track.identifier} '{vc.track.identifier}')**")
            embed.color = self.embedColors.get(ctx.me.id, ctx.me.color)
            await ctx.channel.send(embed=embed)
            await vc.pause()
    
    @commands.guild_only()
    @commands.hybrid_command(description="Resumes the current player")
    async def resume(self, ctx: commands.Context):
        """Unpauses the music player.
        """
        if(not ctx.voice_client):
            return
        vc: wavelink.Player = ctx.voice_client
        if(vc.source == None):
            return
        if(vc.is_playing()):
            embed = discord.Embed(description=f"Resumed **[{vc.track.title}](https://www.youtube.com/watch?v={vc.track.identifier} '{vc.track.identifier}')**")
            embed.color = self.embedColors.get(ctx.me.id, ctx.me.color)
            await ctx.channel.send(embed=embed)
            await vc.resume()
    
    @commands.guild_only()
    @commands.hybrid_command(description="Stops the current player and disconnects from voice")
    async def stop(self, ctx: commands.Context):
        """Stops playing music and disconnects the bot from the voice channel."""
        if(not ctx.voice_client):
            return
        vc: wavelink.Player = ctx.voice_client
        if(vc.source == None):
            return
        if(vc.is_playing()):
            embed = discord.Embed(description=f"Disconnecting")
            embed.color = self.embedColors.get(ctx.me.id, ctx.me.color)
            await ctx.channel.send(embed=embed)
            self.wavequeue[ctx.guild].clear()
            await vc.stop()
            await vc.disconnect()

    @commands.guild_only()
    @commands.hybrid_command(description="Skips the current song")
    async def skip(self, ctx: commands.Context):
        """Skips the current playing song.
        """
        if(not ctx.voice_client):
            return
        vc: wavelink.Player = ctx.voice_client
        if(vc.source == None):
            return
        curr = self.wavequeue[vc.guild].get()
        curr.loop = False
        self.wavequeue[vc.guild].put_at_front(curr)
        await vc.stop()
    
    @commands.guild_only()
    @app_commands.describe(volume="Volume level (Default: 1.0)")
    @commands.hybrid_command(description="Changes the volume of the player")
    async def volume(self, ctx: commands.Context, volume: float=1.0):
        """Set the volume for this guild. (Default 1.0)"""
        if(not ctx.voice_client):
            return
        vc: wavelink.Player = ctx.voice_client
        if(vc.source == None):
            return
        vc.track.loop = False
        await vc.set_volume(volume)
    
    @commands.guild_only()
    @app_commands.describe(position="Time to set to (in seconds)")
    @commands.hybrid_command(description="Sets the current position in the track to the specified time")
    async def set(self, ctx: commands.Context, position: float):
        """Sets the current playback to the specified time (in seconds)"""
        if(not ctx.voice_client):
            return
        vc: wavelink.Player = ctx.voice_client
        if(vc.source == None):
            return
        await vc.seek(position*1000)
    
    @add.before_invoke
    async def ensure_add(self, ctx: commands.Context):
        if(self.wavequeue.get(ctx.guild, None) == None):
            self.wavequeue[ctx.guild] = wavelink.Queue()

    @play.before_invoke
    async def ensure_queue(self, ctx: commands.Context):
        if(self.wavequeue.get(ctx.guild, None) == None):
            self.wavequeue[ctx.guild] = wavelink.Queue()
            self.volume[ctx.guild] = 1.0
    
    def process_sponsorblock(self, sponsorblock_segments: list):
        blocks = []
        sorted_segments = sponsorblock_segments.copy()
        while(len(sorted_segments) > 0):
            start = sorted_segments[0].start
            end = sorted_segments[0].start
            copy_segments = sorted_segments.copy()
            while(len(copy_segments) > 0):
                segment = copy_segments[0]
                if(start <= segment.start <= end):
                    if(segment.end >= end):
                        end = segment.end
                    sorted_segments.remove(segment)
                copy_segments.remove(segment)
            blocks.append([start, end])
        return blocks


async def setup(bot: commands.Bot):
    await bot.add_cog(Lavalink(bot))
