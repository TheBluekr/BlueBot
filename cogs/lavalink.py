import discord
import asyncio
import os

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

class Track(wavelink.YouTubeTrack):
    __slots__ = ("requester", )

    def __init__(self, requester: discord.Member, cls: wavelink.YouTubeTrack):
        super().__init__(cls.data)
        self.requester = requester

class Lavalink(commands.Cog):
    """Music cog to hold Wavelink related commands and listeners."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logger

        self.embed = self.bot.embed

        self.bot.loop.create_task(self.post_init())

        self.sbClient = sponsorblock.Client()

    async def post_init(self):
        await self.bot.wait_until_ready()

        node: wavelink.Node = wavelink.Node(uri='http://lavalink:8080', password='youshallnotpass')
        await wavelink.NodePool.connect(client=self.bot, nodes=[node])
    
    async def get_player(self, guild):
        node = await wavelink.NodePool.get_node()
        return node.get_player(guild)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        """Event fired when a node has finished connecting."""
        self.logger.info(f'Node: <{node.identifier}> is ready!')
    
    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackEventPayload):
        curr: Track = payload.track
        player: wavelink.Player = payload.player
        queue: wavelink.Queue = player.queue

        embed = self.embed.create_embed(curr.requester)
        embed.description = f"**Started playing**:\n**[{curr.title}](https://www.youtube.com/watch?v={curr.identifier} '{curr.identifier}')**"
        if(queue.loop):
            embed.description += " (looped)"
        embed.set_footer(text=f"Requested by: {curr.requester}", icon_url=curr.requester.avatar.url)
        
        await player.channel.send(embed=embed)

        try:
            skips = self.process_sponsorblock(self.sbClient.get_skip_segments(curr.identifier))

            
        except sponsorblock.errors.NotFoundException:
            pass

    @app_commands.guild_only()
    @app_commands.command()
    async def play(self, interaction: discord.Interaction, search: typing.Union[wavelink.YouTubeTrack, wavelink.YouTubeMusicTrack]):
        """Play a song with the given search query. (Also accepts a song after invoke to add to the queue)
        """
        if(not interaction.guild.voice_client):
            vc: wavelink.Player = await interaction.user.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = interaction.guild.voice_client
        if(search != None):
            track = Track(search.id, search.info, requester=interaction.user)
            await vc.queue.put_wait(track)

            embed = self.embed.create_embed(interaction.user)
            embed.description = f"**Added**:\n**[{track.title}](https://www.youtube.com/watch?v={track.identifier} '{track.identifier}')**"
            embed.set_footer(text=f"Requested by: {track.requester}", icon_url=track.requester.avatar.url)
            await vc.channel.send(embed=embed)

            vc.autoplay = True

    @app_commands.guild_only
    @app_commands.command
    async def search(self, interaction: discord.Interaction, query: str):
        tracks = await wavelink.YouTubeTrack.convert(query)

        if(not tracks):
            embed = self.embed.create_embed(interaction.user)
            embed.description = f"Could not find tracks with query: `{query}`"
            return await interaction.response.send_message(embed=embed)
        track = Track(interaction.user, tracks[0])

        if not interaction.guild.voice_client:
            vc: wavelink.Player = await interaction.user.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = interaction.guild.voice_client

        await vc.queue.put_wait(track)

        embed = self.embed.create_embed(interaction.user)
        embed.description = f"**Added**:\n**[{track.title}](https://www.youtube.com/watch?v={track.identifier} '{track.identifier}')**"
        embed.set_footer(text=f"Requested by: {interaction.user}", icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)

        vc.autoplay = True
    
    @search.autocomplete("search")
    async def search_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
        tracks: list[wavelink.YouTubeTrack] = await wavelink.YouTubeTrack.search(current)
        choices = list()

        for track in tracks:
            choices.append(app_commands.Choice(name=track.title, value=track.identifier))

        return choices
    
    def check_voiceclient(self, interaction: discord.Interaction):
        if not interaction.guild.voice_client:
            return False
        vc: wavelink.Player = interaction.guild.voice_client
        if(vc.queue.is_empty and vc.current == None):
            return False
    
    @app_commands.guild_only()
    @app_commands.command(description="Pause the current player")
    @app_commands.check(check_voiceclient)
    async def pause(self, interaction: discord.Interaction):
        """Pauses the music player.
        """
        vc: wavelink.Player = interaction.guild.voice_client
        
        await vc.pause()
        embed = self.embed.create_embed(interaction.user)
        embed.description = f"Paused **[{vc.track.title}](https://www.youtube.com/watch?v={vc.track.identifier} '{vc.track.identifier}')**"
        await interaction.response.send_message(embed=embed)
    
    @app_commands.guild_only()
    @app_commands.command(description="Resumes the current player")
    @app_commands.check(check_voiceclient)
    async def resume(self, interaction: discord.Interaction):
        """Unpauses the music player.
        """
        vc: wavelink.Player = interaction.guild.voice_client

        await vc.resume()
        embed = self.embed.create_embed(interaction.user)
        embed.description = f"Resumed **[{vc.track.title}](https://www.youtube.com/watch?v={vc.track.identifier} '{vc.track.identifier}')**")
        await interaction.response.send_message(embed=embed)
    
    @app_commands.guild_only()
    @app_commands.command(description="Stops the current player and disconnects from voice")
    async def stop(self, interaction: discord.Interaction):
        """Stops playing music and disconnects the bot from the voice channel."""
        embed = self.embed.create_embed(interaction.user)

        if not interaction.guild.voice_client:
            embed.description = "Not connected to voice"
            return await interaction.response.send_message(embed=embed)
        
        vc: wavelink.Player = interaction.guild.voice_client
        
        vc.queue.clear()
        await vc.stop()
        await vc.disconnect()

        embed.description = "Disconnecting"
        await interaction.response.send_message(embed=embed)

    @app_commands.guild_only()
    @app_commands.command(description="Skips the current song")
    @app_commands.check(check_voiceclient)
    async def skip(self, interaction: discord.Interaction):
        """Skips the current playing song.
        """
        vc: wavelink.Player = interaction.guild.voice_client

        await vc.stop(force=True)
    
    @commands.guild_only()
    @app_commands.describe(volume="Volume level (Default: 1.0)")
    @app_commands.command(description="Changes the volume of the player")
    @app_commands.check(check_voiceclient)
    async def volume(self, interaction: discord.Interaction, volume: float=1.0):
        """Set the volume for this guild. (Default 1.0)"""
        vc: wavelink.Player = interaction.guild.voice_client
        await vc.set_volume(volume)

        embed = self.embed.create_embed(interaction.user)
        embed.description = f"Set volume to {volume}"
        await interaction.response.send_message(embed=embed)
    
    @commands.guild_only()
    @app_commands.describe(position="Time to set to (in seconds)")
    @app_commands.command(description="Sets the current position in the track to the specified time")
    @app_commands.check(check_voiceclient)
    async def set(self, interaction: discord.Interaction, position: float):
        """Sets the current playback to the specified time (in seconds)"""
        vc: wavelink.Player = interaction.guild.voice_client
        await vc.seek(position*1000)
    
    def process_sponsorblock(self, sponsorblock_segments: list):
        import operator
        sorted_segments = sorted(sponsorblock_segments, key=operator.attrgetter("start"))
        filter_segments = list()

        start, end = 0.0, 0.0
        
        segment: sponsorblock.Segment
        for segment in sorted_segments:
            if(float(segment.start) == float(segment.end)):
                continue
            elif(start <= float(segment.start) <= end and float(segment.end) > end):
                end = float(segment.end)
            elif(float(segment.start) > end):
                filter_segments.append([start, end])
                start = float(segment.start)
                end = float(segment.end)
        filter_segments.append([start, end])
        return filter_segments

async def setup(bot: commands.Bot):
    await bot.add_cog(Lavalink(bot))
