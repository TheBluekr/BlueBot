import logging
import discord
import asyncio
import random

from discord.ext import commands

from .bismarckgame import BismarckGame
from .bismarckgame.hand import Hand

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.bismarck"
logger = logging.getLogger(__cogname__)

class HandView(discord.ui.View):
    def __init__(self, options, callback, placeholder="Choose a card"):
        super().__init__()
        dropdown = discord.ui.Select(placeholder=placeholder, min_values=4, max_values=4, options=options)
        dropdown.callback = callback
        self.add_item(dropdown)
    
class LobbyView(discord.ui.View):
    def __init__(self, lobby):
        super().__init__()
        self.lobby = lobby
        player = self.lobby.bismarck.players[self.lobby.bismarck.dealer]
        button = discord.ui.Button(label=f"{discord.utils.get(self.bot.get_all_members(), id=player.id)}'s turn", style=discord.ButtonStyle.blurple)
        button.callback = self.addDiscard
        self.add_item(button)
        self.discardView = None
    
    async def updateTurn(self, interaction: discord.Interaction):
        pass
    
    async def addDiscard(self, interaction: discord.Interaction):
        player = self.lobby.bismarck.getPlayer(interaction.user)
        options = []
        for card in player.hand:
            options.append(discord.SelectOption(label=str(card)))
        self.discardView = HandView(options, self.updateDiscard)
        await interaction.response.send_message(content="Select cards to discard", view=self.discardView, ephemeral=True)

    async def updateDiscard(self, interaction: discord.Interaction):
        children = self.discardView.children
        selection = []
        for child in children:
            if(type(child)==discord.ui.Select):
                selection = child.values
            if(type(child) == discord.ui.Button and child.label == "Confirm"):
                self.discardView.remove_item(child)
        button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.green)
        button.callback = self.confirmDiscard
        self.discardView.add_item(button)
        
        discardHand = Hand()
        for card in selection:
            discardHand.addCard(card)
        await interaction.response.edit_message(view=self.discardView, content=f"```Cards selected to discard:\n{str(discardHand)}```\nSelect cards to discard")
    
    async def confirmDiscard(self, interaction: discord.Interaction):
        children = self.discardView.children
        selection = []
        for child in children:
            if(type(child)==discord.ui.Select):
                selection = child.values
            self.discardView.remove_item(child)
        player = self.lobby.bismarck.getPlayer(interaction.user)
        discardHand = Hand()
        for card in selection:
            player.hand.removeCard(card)
            discardHand.addCard(card)
        await interaction.response.edit_message(view=self.discardView, content=f"```Discarded:\n{str(discardHand)}```")

class Lobby:
    def __init__(self, bot, channel):
        self.bot = bot
        self.channelid = channel.id
        self.logger = logger
        self.bismarck = BismarckGame()
        self.view = LobbyView(self)
    
    @property
    def channel(self):
        return discord.utils.get(self.bot.get_all_channels(), id=self.channelid)

    async def start_game(self):
        self.bismarck.newRound()

        await self.channel.send(view=self.view)

    async def play(self):
        pass
    
    def create_embed(self):
        pass

class Bismarck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        self.logger.info(f"Loaded cog {__cogname__}")

        self.lobbies = {}
    
    @commands.guild_only()
    @commands.group(pass_context=True, fallback="create")
    async def bismarck(self, ctx):
        pass

    @bismarck.command()
    async def create(self, ctx: commands.Context):
        lobby = self.lobbies.get(ctx.channel.id)
        if(lobby != None):
            return await ctx.send(f"Lobby already exists for this channel, type `!bismarck join` instead")
        lobby = Lobby(ctx.bot, ctx.channel)
        lobby.bismarck.addPlayer(ctx.author)
        bluebot = discord.utils.get(self.bot.get_all_members(), id=168463608580276224)
        lobby.bismarck.addPlayer(bluebot)
        bluebotDev = discord.utils.get(self.bot.get_all_members(), id=608011373095419904)
        lobby.bismarck.addPlayer(bluebotDev)
        self.lobbies[ctx.channel.id] = lobby
        await ctx.send(f"Created lobby\nFor new players, type `{ctx.bot.command_prefix}bismarck join` to join the lobby")
    
    @bismarck.command()
    async def join(self, ctx: commands.Context):
        lobby = self.lobbies.get(ctx.channel.id)
        if(lobby == None):
            return await ctx.send(f"No lobby exists yet for this channel")
        if(len(lobby.bismarck.players) > 3):
            return await ctx.send(f"No more room")
        if(ctx.author.id in lobby.bismarck.players):
            return
        lobby.bismarck.addPlayer(ctx.author.id)
        await ctx.send(f"Succesfully joined lobby in {ctx.channel} ({len(lobby.bismarck.players)} out of required 3 players)")
    
    @bismarck.command()
    async def addplayer(self, ctx: commands.Context, member: discord.Member):
        lobby = self.lobbies.get(ctx.channel.id)
        if(lobby == None):
            return await ctx.send(f"No lobby exists yet for this channel")
        if(len(lobby.bismarck.players) > 3):
            return await ctx.send(f"No more room")
        if(member.id in lobby.bismarck.players):
            return
        lobby.bismarck.addPlayer(member)
        await ctx.send(f"Succesfully added {member} in {ctx.channel} ({len(lobby.bismarck.players)} out of required 3 players)")

    @bismarck.command()
    async def start(self, ctx: commands.Context):
        lobby = self.lobbies.get(ctx.channel.id)
        if(lobby == None):
            return await ctx.send(f"No lobby exists yet for this channel")
        if(len(lobby.bismarck.players) < 3):
            return await ctx.send(f"Not enough players have joined yet")
        await lobby.start_game()
    
    @bismarck.command()
    async def hand(self, ctx: commands.Context, member: discord.Member=None):
        if(member == None):
            member = ctx.author
        lobby = self.lobbies.get(ctx.channel.id)
        if(lobby == None):
            return await ctx.send(f"No lobby exists yet for this channel")
        player = lobby.bismarck.getPlayer(member)
        await ctx.send(f"```Player: {member}\nHand size: {player.hand.size()}\nHand: {str(player.hand)}```")
    
    @bismarck.command()
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
    await bot.add_cog(Bismarck(bot))
