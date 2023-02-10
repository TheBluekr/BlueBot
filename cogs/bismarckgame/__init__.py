from .deck import Deck
from .card import Card, Suit, Rank
from .player import Player
from .trick import Trick

import discord

class BismarckGame:
    def __init__(self):
        self.deck = Deck()
        self.deck.shuffle()
        
        self.roundNum = -1
        self.trickNum = 0
        self.dealer = 0
        self.currentTrick = Trick()
        self.trickWinner = -1

        self.players = []
    
    def addPlayer(self, player: discord.Member):
        self.players.append(Player(player.id))
    
    def getPlayer(self, player: discord.Member):
        for p in self.players:
            if(p.id == player.id):
                return p
        return None
    
    def getPlayerIndex(self, player: discord.Member):
        for p in self.players:
            if(p.id == player.id):
                return self.players.index(p)
        return None

    def handleScoring(self):
        pass

    def newRound(self):
        self.deck = Deck()
        self.deck.shuffle()
        self.roundNum += 1
        self.trickNum = 0
        self.trickWinner = -1
        self.dealer = (self.roundNum % 4) % len(self.players)
        self.dealCards()
        self.currentTrick = Trick()
        for player in self.players:
            player.discardTricks()

    def dealCards(self):
        # Make sure the dealer is 100% correct
        self.dealer = (self.roundNum % 4) % len(self.players)
        for i in range(4):
            self.players[self.dealer].addCard(self.deck.deal())

        i = 0
        while((self.deck.size()) > 0):
            self.players[i % len(self.players)].addCard(self.deck.deal())
            i += 1

    def evaluateTrick(self):
        self.trickWinner = self.currentTrick.winner
        player = self.players[self.trickWinner]
        player.trickWon(self.currentTrick)
        self.printCurrentTrick()
        self.currentTrick = Trick()

    def playTrick(self):
        # have each player take their turn
        for i in range(start + shift, start + len(self.players)):
            self.printCurrentTrick()
            curPlayerIndex = i % len(self.players)
            self.printPlayer(curPlayerIndex)
            curPlayer = self.players[curPlayerIndex]
            addCard = None

            while addCard is None: # wait until a valid card is passed
                addCard = curPlayer.play()

                # the rules for what cards can be played
                # card set to None if it is found to be invalid
                if addCard != None:

                    # if it is not the first trick and no cards have been played,
                    # set the first card played as the trick suit if it is not a heart
                    # or if hearts have been broken
                    if self.trickNum != 0 and self.currentTrick.cardsInTrick == 0:
                        self.currentTrick.setTrickSuit(addCard)

                    # player tries to play off suit but has trick suit
                    if addCard != None and addCard.suit != self.currentTrick.suit:
                        if curPlayer.hasSuit(self.currentTrick.suit):
                            print("Must play the suit of the current trick.")
                            addCard = None

                    if addCard != None:
                        curPlayer.removeCard(addCard)


            self.currentTrick.addCard(addCard, curPlayerIndex)

        self.evaluateTrick()
        self.trickNum += 1

    # show cards played in current trick
    def printCurrentTrick(self):
        trickStr = '\nCurrent table:\n'
        trickStr += "Trick suit: " + self.currentTrick.suit.__str__() + "\n"
        for i, card in enumerate(self.currentTrick.trick):
            if self.currentTrick.trick[i] != 0:
                trickStr += self.players[i].name + ": " + str(card) + "\n"
            else:
                trickStr += self.players[i].name + ": None\n"
        print(trickStr) 
