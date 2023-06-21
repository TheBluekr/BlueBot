from .deck import Deck
from .card import Card, Suit, Rank
from .player import Player
from .trick import Trick

import discord
from typing import Union

class CardGame:
    def __init__(self):
        self.deck: Deck = Deck()
        self.deck.shuffle()
        
        self.roundNum: int = -1
        self.trickNum: int = 1
        self.dealer: Player = Player(0)
        self.currentTrick: Trick = Trick()
        self.trickWinner: Player = self.dealer

        self.players: list[Player] = []
    
    def addPlayer(self, player: discord.Member) -> None:
        self.players.append(Player(player.id))
    
    def getPlayer(self, player: discord.Member) -> Player|None:
        for p in self.players:
            if(p.id == player.id):
                return p
        return None
    
    def getPlayerIndex(self, player: discord.Member) -> int|None:
        for p in self.players:
            if(p.id == player.id):
                return self.players.index(p)
        return None

    def getPlayerFromIndex(self, index: int) -> Player:
        return self.players[index]

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

    @property
    def currentPlayer(self) -> Player:
        dealerIndex = self.players.index(self.dealer)
        return self.players[(dealerIndex + self.currentTrick.size) % len(self.players)]