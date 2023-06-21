import logging
import discord
import asyncio
import random
from typing import Optional, List

from discord import app_commands
from discord.ext import commands

from .cardgame import CardGame
from .cardgame.deck import Deck
from .cardgame.player import Player
from .cardgame.trick import Trick
from .cardgame.hand import Hand
from .cardgame.card import Card, InvalidCard, Rank, Suit

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.hearts"
logger = logging.getLogger(__cogname__)

class HeartsLobby(CardGame):
    def __init__(self, bot, channel):
        super().__init__()
        self.bot = bot
        self.channelid = channel.id
        self.logger = logger

        self.isActive = False

        self.cookies: Deck = Deck()
        self.cookies.clear()
    
    @property
    def channel(self):
        return discord.utils.get(self.bot.get_all_channels(), id=self.channelid)
    
    def addPlayer(self, player: discord.Member) -> None:
        player: Player = Player(player.id)
        setattr(player, "cookies", list())
        self.players.append(player)
    
    def dealCards(self):
        while(self.deck.size > 0):
            for player in self.players:
                player.addCard(self.deck.deal())

    async def start_game(self, interaction: discord.Interaction):
        if(len(self.players) < 3):
            return
        
        await self.newRound()
        await interaction.followup.send("Started the game")
        await self.evaluateTrick()
        #message = f"Currently {self.currentMember}'s turn"
        #if(self.cookies.size > 0):
            #message += "\nThis trick has a cookie"
        #await self.channel.send(message)
        self.isActive = True
    
    async def newRound(self):
        self.deck = Deck()
        self.deck.shuffle()

        self.cookies: Deck = Deck()
        self.cookies.clear()

        cookies = 52 % len(self.players)        
        for _ in range(cookies):
            self.cookies.addCard(self.deck.deal())
        self.dealCards()

        await self.createTrick()
        
        self.roundNum += 1
        self.dealer = self.players[self.roundNum % len(self.players)]

        #embed = self.create_embed()
        #await self.channel.send(embed=embed)
    
    async def createTrick(self):
        message = f"Current trick no. {self.trickNum}"
        if(self.cookies.size > 0):
            self.currentTrick = Trick(len(self.players)+1)
            message += "\nThis trick has a cookie"
        else:
            self.currentTrick = Trick(len(self.players))
        await self.channel.send(message)
        

    async def evaluateTrick(self):
        if(self.currentTrick.size >= len(self.players)):
            winner: Player = self.players[self.currentTrick.winner]

            message = f"Trick was won by {self.getMemberFromPlayer(winner)}"

            if(self.cookies.size > 0):
                card: Card = self.cookies.deal()
                self.currentTrick.addCard(card, len(self.players))
                message += f"\nCookie was `{card}`"
            
            await self.channel.send(message)
            
            winner.tricksWon.append(self.currentTrick)

            self.trickWinner = winner
            self.trickNum += 1

            await self.createTrick()
        
        if(self.trickNum == (52 // len(self.players))):
            await self.finishRound(self)
        else:
            await self.currentTurnMessage()
    
    async def currentTurnMessage(self):
        message = f"Currently {self.currentMember}'s turn"
        await self.channel.send(message)
    
    async def finishRound(self):
        message = "Round is over"
        assignPoints: list[int] = [0]*len(self.players)
        max: int = 2+13*1+5
        shotTheMoon: Player = Player(0)
        
        for player in self.players:
            playerIndex = self.getPlayerIndex(player)
            for trick in player.tricksWon:
                for card in trick.cards:
                    if(card == Card("J", 0)):
                        # Jack of Clubs is 2
                        assignPoints[playerIndex] += 2
                    if(card.suit == Suit(2)):
                        # Count all hearts
                        assignPoints[playerIndex] += 1
                    if(card == Card("Q", 3)):
                        # Queen of Spades is 5
                        assignPoints[playerIndex] += 5
            player.discardTricks()
            if(assignPoints[playerIndex] == max):
                message += f"\n{self.getMemberFromPlayer(player)} shot the moon!\nEveryone else gets {max} points instead"
                shotTheMoon = player

        for player in self.players:
            playerIndex = self.getPlayerIndex(player)
            if(shotTheMoon != Player(0)):
                if(shotTheMoon == player):
                    continue
                player.points += max
            else:
                player.points += assignPoints[playerIndex]
                message += f"\n{self.getMemberFromPlayer(player)} gets {assignPoints[playerIndex]} points and is now at {player.points}"
        
        await self.channel.send(message)
        await self.newRound()
    
    def create_embed(self):
        embed = discord.Embed(title="Hearts lobby", description="Tricks played:\n```None```")
    
    @property
    def currentMember(self):
        return self.getMemberFromPlayer(self.currentPlayer)
    
    def getMemberFromPlayer(self, player: Player):
        return discord.utils.get(self.bot.get_all_members(), id=player.id)
    
    @property
    def startingPlayer(self) -> Player:
        index = self.getPlayerIndex(self.trickWinner)
        if(index == None):
            index = 0
        return self.players[index]

class Hearts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        self.logger.info(f"Loaded cog {__cogname__}")

        self.lobbies = {}
    
    hearts = app_commands.Group(name="hearts", description="Commands for playing Hearts")

    @hearts.command()
    async def create(self, interaction: discord.Interaction):
        lobby: HeartsLobby = self.lobbies.get(interaction.channel.id)
        if(lobby != None):
            return await interaction.response.send_message(f"Lobby already exists for this channel, type `/hearts join` instead")
        lobby = HeartsLobby(self.bot, interaction.channel)
        lobby.addPlayer(interaction.user)
        #bluebot = discord.utils.get(self.bot.get_all_members(), id=168463608580276224)
        #lobby.addPlayer(bluebot)
        #bluebotDev = discord.utils.get(self.bot.get_all_members(), id=608011373095419904)
        #lobby.addPlayer(bluebotDev)
        self.lobbies[interaction.channel.id] = lobby
        await interaction.response.send_message(f"Created lobby\nFor new players, type `/hearts join` to join the lobby")
    
    @hearts.command()
    async def join(self, interaction: discord.Interaction):
        lobby: HeartsLobby = self.lobbies.get(interaction.channel.id)
        if(lobby == None):
            return await interaction.response.send_message(f"No lobby exists yet for this channel")
        if(lobby.isActive):
            return await interaction.response.send_message(f"Lobby is already playing")
        if(lobby.getPlayer(interaction.user) != None):
            return await interaction.response.send_message("You've already joined the lobby", ephemeral=True)
        lobby.addPlayer(interaction.user)
        await interaction.response.send_message(f"Succesfully joined lobby in {interaction.channel}")
    
    @hearts.command()
    async def addplayer(self, interaction: discord.Interaction, member: discord.Member):
        lobby: HeartsLobby = self.lobbies.get(interaction.channel.id)
        if(lobby == None):
            return await interaction.response.send_message(f"No lobby exists yet for this channel")
        if(lobby.isActive):
            return await interaction.response.send_message(f"Lobby is already playing")
        if(lobby.getPlayer(member) != None):
            return await interaction.response.send_message(f"{member} is already in the lobby")
        lobby.addPlayer(member)
        await interaction.response.send_message(f"Succesfully added {member} in {interaction.channel}")

    @hearts.command()
    async def start(self, interaction: discord.Interaction):
        lobby: HeartsLobby = self.lobbies.get(interaction.channel.id)
        if(lobby == None):
            return await interaction.response.send_message(f"No lobby exists yet for this channel")
        if(len(lobby.players) < 3):
            return await interaction.response.send_message(f"Not enough players have joined yet")
        if(lobby.isActive):
            return await interaction.response.send_message("Lobby is already active")
        if(lobby.getPlayerIndex(interaction.user) > 0):
            return await interaction.response.send_message("Only lobby host can start the game")
        await interaction.response.defer()
        await lobby.start_game(interaction)
    
    @hearts.command()
    async def hand(self, interaction: discord.Interaction):
        lobby: HeartsLobby = self.lobbies.get(interaction.channel.id)
        if(lobby == None):
            return await interaction.response.send_message(f"No lobby exists yet for this channel")
        player = lobby.getPlayer(interaction.user)
        await interaction.response.send_message(f"```Player: {interaction.user}\nHand size: {player.hand.size()}\nHand: {str(player.hand)}```")
    
    @hearts.command()
    async def trick(self, interaction: discord.Interaction):
        lobby: HeartsLobby = self.lobbies.get(interaction.channel.id)
        if(lobby == None):
            return await interaction.response.send_message(f"No lobby exists yet for this channel")
        message = "Cards in trick currently:```"
        startOffset = lobby.getPlayerIndex(lobby.startingPlayer)
        for i in range(len(lobby.players)):
            index = (startOffset+i) % len(lobby.players)
            player: Player = lobby.getPlayerFromIndex(index)
            member: discord.Member = lobby.getMemberFromPlayer(player)
            message += f"{member}: {lobby.currentTrick.getCard(index)}\n"
        message += "```"
        await interaction.response.send_message(message)

    @hearts.command()
    async def play(self, interaction: discord.Interaction, card: str):
        lobby: HeartsLobby = self.lobbies.get(interaction.channel.id)
        if(lobby == None):
            return await interaction.response.send_message(f"No lobby exists yet for this channel")
        hand: Hand = lobby.getPlayer(interaction.user).hand
        playedCard: Card = hand.playCard(card.strip())
        if(playedCard != InvalidCard):
            await interaction.response.send_message(f"{interaction.user} played `{card}`")

            lobby.currentTrick.addCard(playedCard, lobby.getPlayerIndex(interaction.user))
            await lobby.evaluateTrick()
        else:
            await interaction.response.send_message(f"Card not found in hand")
    
    @play.autocomplete("card")
    async def play_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        choices = []
        lobby: HeartsLobby = self.lobbies.get(interaction.channel.id)
        if(lobby == None):
            return []

        current = current.replace("clubs", "♣️")
        current = current.replace("diamonds", "♦️")
        current = current.replace("hearts", "♥")
        current = current.replace("spades", "♠")
        
        player: Player = lobby.getPlayer(interaction.user)

        trick: Trick = lobby.currentTrick

        if(player != lobby.currentPlayer):
            return []

        hand: Hand = player.hand
        if(trick.suit != Suit(-1)):
            suitHand: Hand = hand.fromSuit(trick.suit)
            if(len(suitHand) > 0):
                hand = suitHand
        for card in hand:
            if current.lower() in str(card).lower():
                choices.append(app_commands.Choice(name=str(card), value=str(card)))
        return choices

async def setup(bot):
    await bot.add_cog(Hearts(bot))
