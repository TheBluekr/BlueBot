import logging
import discord
import asyncio
import random

from discord.ext import commands

from .cardgame import CardGame
from .cardgame.deck import Deck
from .cardgame.player import Player
from .cardgame.trick import Trick

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.hearts"
logger = logging.getLogger(__cogname__)

class HandView(discord.ui.View):
    def __init__(self, options, callback, placeholder="Choose a card"):
        super().__init__()
        dropdown = discord.ui.Select(placeholder=placeholder, min_values=1, max_values=1, options=options)
        dropdown.callback = callback
        self.add_item(dropdown)    
        
class HeartsLobby(CardGame):
    def __init__(self, bot, channel):
        super().__init__()
        self.bot = bot
        self.channelid = channel.id
        self.logger = logger
        self.view = self.LobbyView(self)
    
    class LobbyView(discord.ui.View):
        def __init__(self, lobby):
            super().__init__(timeout=None)
            self.lobby = lobby
            button = discord.ui.Button(label=f"{discord.utils.get(self.lobby.bot.get_all_members(), id=self.lobby.dealer.id)}'s turn", style=discord.ButtonStyle.blurple)
            button.callback = self.playCard
            self.add_item(button)
        
        async def playCard(self, interaction: discord.Interaction):
            pass
    
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

        embed = self.create_embed()
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
    
    @commands.guild_only()
    @commands.group(pass_context=True, fallback="create")
    async def hearts(self, ctx):
        pass

    @hearts.command()
    async def create(self, ctx: commands.Context):
        lobby = self.lobbies.get(ctx.channel.id)
        if(lobby != None):
            return await ctx.send(f"Lobby already exists for this channel, type `{ctx.bot.command_prefix}hearts join` instead")
        lobby = HeartsLobby(ctx.bot, ctx.channel)
        lobby.addPlayer(ctx.author)
        bluebot = discord.utils.get(self.bot.get_all_members(), id=168463608580276224)
        lobby.addPlayer(bluebot)
        bluebotDev = discord.utils.get(self.bot.get_all_members(), id=608011373095419904)
        lobby.addPlayer(bluebotDev)
        self.lobbies[ctx.channel.id] = lobby
        await ctx.send(f"Created lobby\nFor new players, type `{ctx.bot.command_prefix}hearts join` to join the lobby")
    
    @hearts.command()
    async def join(self, ctx: commands.Context):
        lobby = self.lobbies.get(ctx.channel.id)
        if(lobby == None):
            return await ctx.send(f"No lobby exists yet for this channel")
        if(len(lobby.players) > 4):
            return await ctx.send(f"No more room")
        if(ctx.author.id in lobby.players):
            return
        lobby.addPlayer(ctx.author.id)
        await ctx.send(f"Succesfully joined lobby in {ctx.channel} ({len(lobby.players)} out of required 4 players)")
    
    @hearts.command()
    async def addplayer(self, ctx: commands.Context, member: discord.Member):
        lobby = self.lobbies.get(ctx.channel.id)
        if(lobby == None):
            return await ctx.send(f"No lobby exists yet for this channel")
        if(len(lobby.players) > 4):
            return await ctx.send(f"No more room")
        if(member.id in lobby.players):
            return
        lobby.addPlayer(member)
        await ctx.send(f"Succesfully added {member} in {ctx.channel} ({len(lobby.bismarck.players)} out of required 3 players)")

    @hearts.command()
    async def start(self, ctx: commands.Context):
        lobby = self.lobbies.get(ctx.channel.id)
        if(lobby == None):
            return await ctx.send(f"No lobby exists yet for this channel")
        if(len(lobby.players) < 4):
            return await ctx.send(f"Not enough players have joined yet")
        await lobby.start_game()
    
    @hearts.command()
    async def hand(self, ctx: commands.Context, member: discord.Member=None):
        if(member == None):
            member = ctx.author
        lobby = self.lobbies.get(ctx.channel.id)
        if(lobby == None):
            return await ctx.send(f"No lobby exists yet for this channel")
        player = lobby.getPlayer(member)
        await ctx.send(f"```Player: {member}\nHand size: {player.hand.size()}\nHand: {str(player.hand)}```")
    
    @hearts.command()
    async def play(self, ctx: commands.Context, card: str):
        lobby = self.lobbies.get(ctx.channel.id)
        if(lobby == None):
            return await ctx.send(f"No lobby exists yet for this channel")
        hand = lobby.players[ctx.author.id][0]
        if(card.strip() in str(hand)):
            await ctx.send(f"Played {card.strip()}")
        else:
            await ctx.send(f"Card not found in hand")

async def setup(bot):
    await bot.add_cog(Hearts(bot))
