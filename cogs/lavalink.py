import discord
import asyncio

import json

from discord.ext import commands
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

        self.bot.loop.create_task(self.connect_nodes())

        self.wavequeue = {}
        self.sbClient = sponsorblock.Client()

        self.logger = logger

    async def connect_nodes(self):
        """Connect to our Lavalink nodes."""
        await self.bot.wait_until_ready()

        await wavelink.NodePool.create_node(bot=self.bot, host='lavalink', port=8080, password='youshallnotpass')
    
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
        if(curr.identifier != track.identifier):
            await player.channel.send("Mismatch occured between expected and playing track, this is not intended.\nPlease contact the bot author if this occured.")
            await player.stop()
            return
        self.logger.info(f"Started playing: {curr.title} ({curr.identifier})")

        segments = self.sbClient.get_skip_segments(curr.identifier)
        segments.sort(key=lambda x: x.start)

        skips = self.process_sponsorblock(segments)

        await player.set_volume(0.2)

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
        embed = discord.Embed(description=f"**Started playing**:\n**[{track.title}](https://www.youtube.com/watch?v={track.identifier} '{track.identifier}')**")
        embed.set_footer(text=f"Requested by: {curr.requester}", icon_url=curr.requester.avatar.url)
        
        await player.channel.send(embed=embed)

        if(curr.sb):
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

    @commands.Cog.listener('on_wavelink_track_end')
    @commands.Cog.listener('on_wavelink_track_exception')
    @commands.Cog.listener('on_wavelink_track_stuck')
    async def on_player_stop(self, player: wavelink.Player, track, reason):
        self.logger.info(f"Finished playing")
        if(self.wavequeue[player.guild].count > 0):
            nexttrack = self.wavequeue[player.guild].get()
            self.wavequeue[player.guild].put_at_front(nexttrack)
            player.play(nexttrack)
        else:
            await player.disconnect()

    @commands.command()
    async def lplay(self, ctx: commands.Context, *, search: typing.Union[wavelink.YouTubeTrack, wavelink.YouTubeMusicTrack, wavelink.SoundCloudTrack]=None, loop: bool=False, sponsorblock: bool=True):
        """Play a song with the given search query.

        If not connected, connect to our voice channel.
        """
        if(not ctx.voice_client):
            vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = ctx.voice_client

        if(search != None):
            track = Track(search.id, search.info, requester=ctx.author, sponsorblock=sponsorblock, loop=loop)
            self.wavequeue[ctx.guild].put(track)

            embed = discord.Embed(description=f"**Added**:\n**[{track.title}](https://www.youtube.com/watch?v={track.identifier} '{track.identifier}')**")
            embed.set_footer(text=f"Requested by: {track.requester}", icon_url=track.requester.avatar.url)
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
    
    @commands.command()
    async def lpause(self, ctx: commands.Context):
        if not ctx.voice_client:
            return
        vc: wavelink.Player = ctx.voice_client
        if(vc.source == None):
            return
        if(vc.is_playing()):
            embed = discord.Embed(description=f"Paused **{vc.track.title}**")
            await ctx.channel.send(embed=embed)
            await vc.pause()
    
    @commands.command()
    async def lresume(self, ctx: commands.Context):
        if(not ctx.voice_client):
            return
        vc: wavelink.Player = ctx.voice_client
        if(vc.source == None):
            return
        if(vc.is_playing()):
            embed = discord.Embed(description=f"Resumed **{vc.track.title}**")
            await ctx.channel.send(embed=embed)
            await vc.resume()
    
    @commands.command()
    async def lstop(self, ctx: commands.Context):
        if(not ctx.voice_client):
            return
        vc: wavelink.Player = ctx.voice_client
        if(vc.source == None):
            return
        if(vc.is_playing()):
            embed = discord.Embed(description=f"Stopped playing")
            await ctx.channel.send(embed=embed)
            self.wavequeue[ctx.guild].clear()
            await vc.stop()
            await vc.disconnect()

    @commands.command()
    async def lskip(self, ctx: commands.Context):
        if(not ctx.voice_client):
            return
        vc: wavelink.Player = ctx.voice_client
        if(vc.source == None):
            return
        await vc.stop()
    
    @commands.command()
    async def lvolume(self, ctx: commands.Context, volume: float=100.0):
        if(not ctx.voice_client):
            return
        vc: wavelink.Player = ctx.voice_client
        if(vc.source == None):
            return
        await vc.set_volume(volume)
    
    @commands.command()
    async def lseek(self, ctx: commands.Context, position: float):
        if(not ctx.voice_client):
            return
        vc: wavelink.Player = ctx.voice_client
        if(vc.source == None):
            return
        await vc.seek(position*1000)
    
    @lplay.before_invoke
    async def ensure_queue(self, ctx: commands.Context):
        self.wavequeue[ctx.guild] = wavelink.Queue()
    
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
