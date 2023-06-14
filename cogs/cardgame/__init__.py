from .deck import Deck
from .card import Card, Suit, Rank
from .player import Player
from .trick import Trick

import discord

class CardGame:
    def __init__(self):
        self.deck: Deck = Deck()
        self.deck.shuffle()
        
        self.roundNum: int = -1
        self.trickNum: int = 0
        self.dealer: Player = Player(0)
        self.currentTrick: Trick = Trick()
        self.trickWinner: Player = Player(0)

        self.players: list = []
    
    def addPlayer(self, player: discord.Member) -> None:
        self.players.append(Player(player.id))
    
    def getPlayer(self, player: discord.Member) -> Player:
        for p in self.players:
            if(p.id == player.id):
                return p
        return None
    
    def getPlayerIndex(self, player: discord.Member) -> int:
        for p in self.players:
            if(p.id == player.id):
                return self.players.index(p)
        return None

    def handleScoring(self):
        raise NotImplementedError

    def newRound(self):
        raise NotImplementedError

    def dealCards(self):
        raise NotImplementedError

    def evaluateTrick(self):
        raise NotImplementedError

    def playTrick(self):
        raise NotImplementedError

    # show cards played in current trick
    def returnCurrentTrick(self):
        raise NotImplementedError
