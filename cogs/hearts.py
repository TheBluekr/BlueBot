import logging
import discord
import asyncio
import random

from discord.ext import commands

__author__ = "TheBluekr#2702"
__cogname__ = "bluebot.cogs.hearts"
logger = logging.getLogger(__cogname__)

deck = {0: '♣️2', 1: '♣️3', 2: '♣️4', 3: '♣️5', 4: '♣️6', 5: '♣️7', 6: '♣️8', 7: '♣️9', 8: '♣️10', 9: '♣️J', 10: '♣️Q', 11: '♣️K', 12: '♣️A', 13: '♦️2', 14: '♦️3', 15: '♦️4', 16: '♦️5', 17: '♦️6', 18: '♦️7', 19: '♦️8', 20: '♦️9', 21: '♦️10', 22: '♦️J', 23: '♦️Q', 24: '♦️K', 25: '♦️A', 26: '♥2', 27: '♥3', 28: '♥4', 29: '♥5', 30: '♥6', 31: '♥7', 32: '♥8', 33: '♥9', 34: '♥10', 35: '♥J', 36: '♥Q', 37: '♥K', 38: '♥A', 39: '♠2', 40: '♠3', 41: '♠4', 42: '♠5', 43: '♠6', 44: '♠7', 45: '♠8', 46: '♠9', 47: '♠10', 48: '♠J', 49: '♠Q', 50: '♠K', 51: '♠A'}
deck_inv = {'♣️2': 0, '♣️3': 1, '♣️4': 2, '♣️5': 3, '♣️6': 4, '♣️7': 5, '♣️8': 6, '♣️9': 7, '♣️10': 8, '♣️J': 9, '♣️Q': 10, '♣️K': 11, '♣️A': 12, '♦️2': 13, '♦️3': 14, '♦️4': 15, '♦️5': 16, '♦️6': 17, '♦️7': 18, '♦️8': 19, '♦️9': 20, '♦️10': 21, '♦️J': 22, '♦️Q': 23, '♦️K': 24, '♦️A': 25, '♥2': 26, '♥3': 27, '♥4': 28, '♥5': 29, '♥6': 30, '♥7': 31, '♥8': 32, '♥9': 33, '♥10': 34, '♥J': 35, '♥Q': 36, '♥K': 37, '♥A': 38, '♠2': 39, '♠3': 40, '♠4': 41, '♠5': 42, '♠6': 43, '♠7': 44, '♠8': 45, '♠9': 46, '♠10': 47, '♠J': 48, '♠Q': 49, '♠K': 50, '♠A': 51}

class Hand:
    def __init__(self, cards: list):
        self._cards = cards
        self.logger = logger

        self._cards.sort()

    def __str__(self):
        returnlist = [deck[card] for card in self._cards]
        return ", ".join(returnlist)

    def __iter__(self):
        return iter(self._cards)

    @property
    def clubs(self):
        return [deck[card] for card in self._cards if card.startswith("♣️")]
    
    @property
    def diamonds(self):
        return [deck[card] for card in self._cards if card.startswith("♦️")]

    @property
    def hearts(self):
        return [deck[card] for card in self._cards if card.startswith("♥")]

    @property
    def spades(self):
        return [deck[card] for card in self._cards if card.startswith("♠")]
    
class Lobby:
    def __init__(self, bot, host):
        self.bot = bot
        self.logger = logger

        self.active = False
        self.rounds = 0
        self.turn = 0

        self.hands = []
        self.deal()

        self.players = {host.id: [Hand(self.hands.pop()), 0]}
        self.rounds = []
    
    def deal(self):
        #total = [i for i in range(len(deck.keys()))] # Full deck
        total = [i for i in range(len(deck.keys())) if (i % 13) > 5] # Starting from 7

        self.hands = []
        random.shuffle(total)
        for i in range(0, len(total), int(len(total)/4)):
            self.hands.append(total[i:i + int(len(total)/4)])

class Hearts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        self.logger.info(f"Loaded cog {__cogname__}")

        self.lobbies = {}
    
    @commands.guild_only()
    @commands.group(pass_context=True)
    async def hearts(self, ctx):
        pass

    @hearts.command()
    async def create(self, ctx):
        if(self.lobbies.get(ctx.channel.id, None) != None):
            return await ctx.send(f"Lobby already exists for this channel, type `!hearts join` instead")
        self.lobbies[ctx.channel.id] = Lobby(self.bot, ctx.author)
        await ctx.send(f"Created lobby\nType `!hearts join` to join the lobby")
    
    @hearts.command()
    async def join(self, ctx):
        if(self.lobbies.get(ctx.channel.id, None) == None):
            return await ctx.send(f"No lobby exists yet for this channel")
        lobby = self.lobbies[ctx.channel.id]
        if(len(lobby.players.keys()) > 4):
            return await ctx.send(f"No more room")
        lobby.players[ctx.author.id][0] = Hand(lobby.hands.pop())
        await ctx.send(f"Succesfully joined lobby in {ctx.channel}")
    
    @hearts.command()
    async def start(self, ctx):
        if(self.lobbies.get(ctx.channel.id, None) == None):
            return await ctx.send(f"No lobby exists yet for this channel")
        lobby = self.lobbies[ctx.channel.id]
        if(len(lobby.players.keys()) < 4):
            return await ctx.send(f"Not enough players")
        lobby.active = True
    
    @hearts.command()
    async def hand(self, ctx):
        lobby = self.lobbies.get(ctx.channel.id, None)
        await ctx.send(f"```{str(lobby.players[ctx.author.id][0])}```")
    
    @hearts.command()
    async def play(self, ctx, *, card:str):
        lobby = self.lobbies.get(ctx.channel.id, None)
        if(lobby == None):
            return await ctx.send(f"No lobby exists yet for this channel")
        hand = lobby.players[ctx.author.id][0]
        if(card.strip() in str(hand)):
            await ctx.send(f"Played {card.strip()}")
        else:
            await ctx.send(f"Card not found in hand")

async def setup(bot):
    await bot.add_cog(Hearts(bot))
