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

class Lavalink(commands.Cog):
    """Music cog to hold Wavelink related commands and listeners."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logger
        self.logger.info(f"Loaded cog {__cogname__}")

        self.embed = self.bot.embed

        self.sbClient = sponsorblock.Client()

    async def cog_load(self):
        try:
            node: wavelink.Node = wavelink.Node(uri='http://lavalink:2333', password='youshallnotpass')
            await wavelink.Pool.connect(nodes=[node], client=self.bot)
        except Exception as e:
            if hasattr(e, 'message'):
                self.logger.error(e.message)
            else:
                self.logger.error(e)
            await self.bot.remove_cog(__class__.__name__)
    
    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        """Event fired when a node has finished connecting."""
        self.logger.info(f'Node: <{payload.node.identifier}> is ready!')
    
    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        player: wavelink.Player = payload.player
        queue: wavelink.Queue = player.queue
        curr: wavelink.Playable = player.current

        requester = self.bot.get_user(curr.extras.requester_id)

        embed: discord.Embed = self.embed.create_embed(requester)
        #if(curr.source == "youtube"):
            #url = "https://www.youtube.com/watch?v="
        embed.description = f"**Started playing**:\n**[{curr.title}]({curr.uri} '{curr.identifier}')**"
        if(queue.mode == wavelink.QueueMode.loop):
            embed.description += " (looped)"
        embed.set_footer(text=f"Requested by: {requester}", icon_url=requester.avatar.url)
        
        await player.channel.send(embed=embed)

        try:
            skips = self.process_sponsorblock(self.sbClient.get_skip_segments(curr.identifier))
            skips = []
            while skips:
                if(float(player.position/1000) > skips[0][0]):
                   await player.seek(int(skips[0][1]*1000.0))
                   del skips[0]
                await asyncio.sleep(0.5)
        except sponsorblock.errors.NotFoundException:
            pass
    
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        player: wavelink.Player = payload.player
        queue: wavelink.Queue = player.queue

        if(len(queue) == 0):
            player.cleanup()
            await player.disconnect()

    music = app_commands.Group(name="music", description="Commands for playing music")

    def check_voice_user():
        async def predicate(interaction: discord.Interaction):
            if not interaction.user.voice:
                return False
            return True
        return app_commands.check(predicate)
    
    def check_user_perms():
        async def predicate(interaction: discord.Interaction):
            if not interaction.user.guild_permissions.administrator:
                return False
            return True
        return app_commands.check(predicate)

    @app_commands.guild_only()
    @check_voice_user()
    @music.command()
    async def play(self, interaction: discord.Interaction, url: str=None):
        """Play a song with the given search query. (Also accepts a song after invoke to add to the queue)
        """
        embed: discord.Embed = self.embed.create_embed(interaction.user)

        if(not interaction.guild.voice_client):
            vc: wavelink.Player = await interaction.user.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = interaction.guild.voice_client

        if(url):
            tracks: wavelink.Search = await wavelink.Playable.search(url)
            if(not tracks):
                embed.description = f"Could not find tracks with url: `{url}`"
                return await interaction.response.send_message(embed=embed)
            
            if isinstance(tracks, wavelink.Playlist):
                embed.description = f"Playlist support hasn't been added yet"
                return await interaction.response.send_message(embed=embed)
            else:
                track: wavelink.Playable = tracks[0]
                track.extras = {"requester_id": interaction.user.id}

                embed.description = f"**Added**:\n**[{track.title}](https://www.youtube.com/watch?v={track.identifier} '{track.identifier}')**"
                embed.set_footer(text=f"Requested by: {interaction.user}", icon_url=interaction.user.avatar.url)
                await interaction.response.send_message(embed=embed)

                await vc.queue.put_wait(track)
        else:
            await interaction.response.defer(thinking=False)
        if not vc.playing:
            # Play now since we aren't playing anything...
            await vc.play(vc.queue.get(), volume=40)
            vc.autoplay = wavelink.AutoPlayMode.partial

    @app_commands.guild_only()
    @check_voice_user()
    @music.command()
    async def add(self, interaction: discord.Interaction, url: str):
        """Add a song with the given search query. (Also accepts a song after invoke to add to the queue)
        """
        embed: discord.Embed = self.embed.create_embed(interaction.user)

        if(not interaction.guild.voice_client):
            vc: wavelink.Player = await interaction.user.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = interaction.guild.voice_client

        tracks: wavelink.Search = await wavelink.Playable.search(url)

        if(not tracks):
            embed.description = f"Could not find tracks with url: `{url}`"
            return await interaction.response.send_message(embed=embed)
        
        if isinstance(tracks, wavelink.Playlist):
            embed.description = f"Playlist support hasn't been added yet"
            return await interaction.response.send_message(embed=embed)
        else:
            track: wavelink.Playable = tracks[0]
            track.extras = {"requester_id": interaction.user.id}
            
            embed.description = f"**Added**:\n**[{track.title}]({track.uri} '{track.identifier}')**"
            embed.set_footer(text=f"Requested by: {interaction.user}", icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)
            await vc.queue.put_wait(track)

        if(not vc.playing):
            await vc.play(vc.queue.get(), volume=40)

            vc.autoplay = wavelink.AutoPlayMode.partial

    @app_commands.guild_only()
    @check_voice_user()
    @music.command()
    @app_commands.choices(source=[
        app_commands.Choice(name="YouTube", value="YouTube"),
        #app_commands.Choice(name="YouTube Music", value="YouTubeMusic"),
        #app_commands.Choice(name="SoundCloud", value="SoundCloud"),
        #app_commands.Choice(name="Spotify", value="spsearch"),
        ])
    async def search(self, interaction: discord.Interaction, source: app_commands.Choice[str], query: str):
        embed: discord.Embed = self.embed.create_embed(interaction.user)

        if(not interaction.guild.voice_client):
            vc: wavelink.Player = await interaction.user.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = interaction.guild.voice_client

        #if(source.value.endswith("search")):
            #tracks: list[wavelink.Playable] = await wavelink.Playable.search(query, source=source.value)
            #self.logger.info(f"Searched spotify track with {query}")
        #else:
            #tracks: list[wavelink.Playable] = await wavelink.Playable.search(f"{query}", source=getattr(wavelink.TrackSource, source.value))
        tracks: list[wavelink.Playable] = await wavelink.Playable.search(query)
        
        if(not tracks):
            embed.description = f"Could not find tracks with url: `{query}`"
            return await interaction.response.send_message(embed=embed)
        
        track = tracks[0]
        track.extras = {"requester_id": interaction.user.id}
            
        embed.description = f"**Added**:\n**[{track.title}]({track.uri} '{track.identifier}')**"
        embed.set_footer(text=f"Requested by: {interaction.user}", icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        await vc.queue.put_wait(track)
        
        if(not vc.playing):
            await vc.play(vc.queue.get(), volume=40)

            vc.autoplay = wavelink.AutoPlayMode.partial

    @search.autocomplete("query")
    async def query_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
        choices = list()
        if(current == ""):
            return choices
        if(interaction.namespace.source.endswith("search")):
            tracks: list[wavelink.Playable] = await wavelink.Playable.search(f"{current}") #, source=interaction.namespace.source)
        else:
            tracks: list[wavelink.Playable] = await wavelink.Playable.search(f"{current}") #, source=getattr(wavelink.TrackSource, interaction.namespace.source))

        tracks = tracks[:5]
        for track in tracks:
            if(track.uri):
                choices.append(app_commands.Choice(name=f"{track.author} - {track.title}", value=track.uri))
        return choices
    
    def check_voiceclient():
        async def predicate(interaction: discord.Interaction):
            if not interaction.guild.voice_client:
                return False
            vc: wavelink.Player = interaction.guild.voice_client
            if(not vc.playing):
                return False
            return True
        return app_commands.check(predicate)
    
    @app_commands.guild_only()
    @check_voice_user()
    @check_voiceclient()
    @check_user_perms()
    @music.command(description="Pause the current player")
    async def pause(self, interaction: discord.Interaction):
        """Pauses the music player.
        """
        vc: wavelink.Player = interaction.guild.voice_client
        
        await vc.pause()
        embed = self.embed.create_embed(interaction.user)
        embed.description = f"Paused **[{vc.track.title}](https://www.youtube.com/watch?v={vc.track.identifier} '{vc.track.identifier}')**"
        await interaction.response.send_message(embed=embed)
    
    @app_commands.guild_only()
    @check_voice_user()
    @check_voiceclient()
    @check_user_perms()
    @music.command(description="Resumes the current player")
    async def resume(self, interaction: discord.Interaction):
        """Unpauses the music player.
        """
        vc: wavelink.Player = interaction.guild.voice_client

        await vc.resume()
        embed = self.embed.create_embed(interaction.user)
        embed.description = f"Resumed **[{vc.track.title}](https://www.youtube.com/watch?v={vc.track.identifier} '{vc.track.identifier}')**"
        await interaction.response.send_message(embed=embed)
    
    @app_commands.guild_only()
    @check_voice_user()
    @check_user_perms()
    @music.command(description="Stops the current player and disconnects from voice")
    async def stop(self, interaction: discord.Interaction):
        """Stops playing music and disconnects the bot from the voice channel.
        """
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
    @check_voice_user()
    @check_voiceclient()
    @check_user_perms()
    @music.command(description="Skips the current song")
    async def skip(self, interaction: discord.Interaction):
        """Skips the current playing song.
        """
        embed = self.embed.create_embed(interaction.user)

        if not interaction.guild.voice_client:
            embed.description = "Not connected to voice"
            return await interaction.response.send_message(embed=embed)
        
        vc: wavelink.Player = interaction.guild.voice_client

        await vc.stop(force=True)

        embed.description = "Skipped current song"

        await interaction.response.send_message(embed=embed)
    
    @commands.guild_only()
    @check_voice_user()
    @check_voiceclient()
    @check_user_perms()
    @app_commands.describe(volume="Volume level (Default: 1.0)")
    @music.command(description="Changes the volume of the player")
    async def volume(self, interaction: discord.Interaction, volume: app_commands.Range[float, 0.0, 20.0]=None):
        """Set the volume for this guild. (Default 1.0)"""
        vc: wavelink.Player = interaction.guild.voice_client

        embed = self.embed.create_embed(interaction.user)
        if(volume):
            await vc.set_volume(round(volume*50))
            embed.description = f"Set volume to {round(volume*50*2)}%"
        else:
            embed.description = f"Volume is: {vc.volume*2}%"
        await interaction.response.send_message(embed=embed)
    
    @commands.guild_only()
    @check_voice_user()
    @check_voiceclient()
    @check_user_perms()
    @app_commands.describe(position="Time to set to (in seconds)")
    @music.command(description="Sets the current position in the track to the specified time")
    async def set(self, interaction: discord.Interaction, position: float):
        """Sets the current playback to the specified time (in seconds)"""
        embed = self.embed.create_embed(interaction.user)

        if not interaction.guild.voice_client:
            embed.description = "Not connected to voice"
            return await interaction.response.send_message(embed=embed)
        
        vc: wavelink.Player = interaction.guild.voice_client
        await vc.seek(round(position*1000.0))

        embed.description = f"Set playback to {position}s"

        await interaction.response.send_message(embed=embed)
    
    @commands.guild_only()
    @check_voice_user()
    @check_voiceclient()
    @check_user_perms()
    @app_commands.describe(loop="Bool whether to loop")
    @music.command(description="Toggle whether the current song should loop")
    async def loop(self, interaction: discord.Interaction, loop: bool):
        """Toggle whether the current song should loop"""
        vc: wavelink.Player = interaction.guild.voice_client
        vc.queue.loop = loop
        await interaction.response.send_message(f"Set loop state to {vc.queue.loop}")
    
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

    @app_commands.guild_only()
    @check_voiceclient()
    @music.command()
    async def queue(self, interaction: discord.Interaction):
        """Return queue for voice player"""
        vc: wavelink.Player = interaction.guild.voice_client

        embed = self.embed.create_embed(interaction.user)
        
        if(vc.current):
            embed.description = f"**Currently playing**:\n**[{vc.current.title}](https://www.youtube.com/watch?v={vc.current.identifier} '{vc.current.identifier}')**\n"
        
        if(vc.queue.count > 0):
            embed.description += "\n**Next up**:"
            for index, track in enumerate(vc.queue):
                if(index > 5):
                    embed.description += f"\nAnd {vc.queue.count-5} more"
                    break
                embed.description += f"\n**[{track.title}](https://www.youtube.com/watch?v={track.identifier} '{track.identifier}')**"

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Lavalink(bot))
