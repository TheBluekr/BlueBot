import logging
import discord
import asyncio
import random
import typing

from discord import app_commands
from discord.ext import commands

from .cardgame import CardGame
from .cardgame.deck import Deck
from .cardgame.player import Player
from .cardgame.trick import Trick
from .cardgame.hand import Hand

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.hearts"
logger = logging.getLogger(__cogname__)

class HandView(discord.ui.View):
    def __init__(self, options, callback, placeholder="Choose a card"):
        super().__init__()
        dropdown = discord.ui.Select(placeholder=placeholder, min_values=1, max_values=1, options=options)
        dropdown.callback = callback
        self.add_item(dropdown)

class LobbyView(discord.ui.View):
    def __init__(self, lobby):
        super().__init__(timeout=None)
        self.lobby = lobby
        button = discord.ui.Button(label=f"{discord.utils.get(self.lobby.bot.get_all_members(), id=self.lobby.dealer.id)}'s turn", style=discord.ButtonStyle.blurple)
        button.callback = self.playCard
        self.add_item(button)
    
    async def playCard(self, interaction: discord.Interaction):
        pass
        
class HeartsLobby(CardGame):
    def __init__(self, bot, channel):
        super().__init__()
        self.bot = bot
        self.channelid = channel.id
        self.logger = logger
        self.view = LobbyView(self)
    
    @property
    def channel(self):
        return discord.utils.get(self.bot.get_all_channels(), id=self.channelid)

    async def start_game(self):
        if(len(self.players) < 4):
            return
        
        self.newRound()
    
    async def newRound(self):
        self.deck = Deck()
        self.deck.shuffle()
        self.dealCards()
        self.roundNum += 1
        self.dealer = self.players[self.roundNum % len(self.players)]

        embed = self.create_embed(self.bot.user)
        await self.channel.send(embed=embed, view=self.view)
    
    async def finishRound(self):
        # Handle scoring
        pass
        
    async def dealCards(self):
        for player in self.players:
            player.addCard(self.deck.deal())
    
    def create_embed(self):
        embed = discord.Embed(title="Hearts lobby", description="Tricks played:\n```None```")

class Hearts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        self.logger.info(f"Loaded cog {__cogname__}")

        self.lobbies = {}
    
    hearts = app_commands.Group(name="hearts", description="Commands for playing Hearts")

    @hearts.command()
    async def create(self, interaction: discord.Interaction):
        lobby = self.lobbies.get(interaction.channel.id)
        if(lobby != None):
            return await interaction.response.send_message(f"Lobby already exists for this channel, type `/hearts join` instead")
        lobby = HeartsLobby(self.bot, interaction.channel)
        lobby.addPlayer(interaction.user)
        bluebot = discord.utils.get(self.bot.get_all_members(), id=168463608580276224)
        lobby.addPlayer(bluebot)
        bluebotDev = discord.utils.get(self.bot.get_all_members(), id=608011373095419904)
        lobby.addPlayer(bluebotDev)
        self.lobbies[interaction.channel.id] = lobby
        await interaction.response.send_message(f"Created lobby\nFor new players, type `/hearts join` to join the lobby")
    
    @hearts.command()
    async def join(self, interaction: discord.Interaction):
        lobby = self.lobbies.get(interaction.channel.id)
        if(lobby == None):
            return await interaction.response.send_message(f"No lobby exists yet for this channel")
        if(len(lobby.players) > 4):
            return await interaction.response.send_message(f"No more room")
        if(interaction.user.id in lobby.players):
            return
        lobby.addPlayer(interaction.user.id)
        await interaction.response.send_message(f"Succesfully joined lobby in {interaction.channel} ({len(lobby.players)} out of required 4 players)")
    
    @hearts.command()
    async def addplayer(self, interaction: discord.Interaction, member: discord.Member):
        lobby = self.lobbies.get(interaction.channel.id)
        if(lobby == None):
            return await interaction.response.send_message(f"No lobby exists yet for this channel")
        if(len(lobby.players) > 4):
            return await interaction.response.send_message(f"No more room")
        if(member.id in lobby.players):
            return
        lobby.addPlayer(member)
        await interaction.response.send_message(f"Succesfully added {member} in {interaction.channel} ({len(lobby.players)} out of required 4 players)")

    @hearts.command()
    async def start(self, interaction: discord.Interaction):
        lobby = self.lobbies.get(interaction.channel.id)
        if(lobby == None):
            return await interaction.response.send_message(f"No lobby exists yet for this channel")
        if(len(lobby.players) < 4):
            return await interaction.response.send_message(f"Not enough players have joined yet")
        await lobby.start_game()
    
    @hearts.command()
    async def hand(self, interaction: discord.Interaction):
        lobby = self.lobbies.get(interaction.channel.id)
        if(lobby == None):
            return await interaction.response.send_message(f"No lobby exists yet for this channel")
        player = lobby.getPlayer(interaction.user)
        await interaction.response.send_message(f"```Player: {interaction.user}\nHand size: {player.hand.size()}\nHand: {str(player.hand)}```")
    
    @hearts.command()
    async def play(self, interaction: discord.Interaction, card: str):
        lobby = self.lobbies.get(interaction.channel.id)
        if(lobby == None):
            return await interaction.response.send_message(f"No lobby exists yet for this channel")
        hand = lobby.players[interaction.user.id][0]
        if(card.strip() in str(hand)):
            await interaction.response.send_message(f"Played {card.strip()}")
        else:
            await interaction.response.send_message(f"Card not found in hand")
    
    @play.autocomplete("card")
    async def play_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
        choices = list()
        lobby: HeartsLobby = self.lobbies.get(interaction.channel.id)
        if(lobby == None):
            return choices
        player: Player = lobby.getPlayer(interaction.user)
        hand: Hand = player.hand
        for card in hand:
            if current.lower() in str(card).lower():
                choices.append(str(card))
        return choices

async def setup(bot):
    await bot.add_cog(Hearts(bot))
