from random import randint
from .card import Card, Suit, Rank
from typing import Union

clubs = 0
diamonds = 1
hearts = 2
spades = 3
suits = ["♣️", "♦️", "♥", "♠"]

class Hand:
    def __init__(self):
        self.clubs: list[Card] = []
        self.diamonds: list[Card] = []
        self.hearts: list[Card] = []
        self.spades: list[Card] = []

    def size(self) -> int:
        return len(self.clubs) + len(self.diamonds) + len(self.hearts) + len(self.spades)

    def addCard(self, card: Card) -> None:
        if(type(card) == str):
            card = self.strToCard(card)

        if card.suit == Suit(clubs):
            self.clubs.append(card)
            self.clubs.sort()
        elif card.suit == Suit(diamonds):
            self.diamonds.append(card)
            self.diamonds.sort()
        elif card.suit == Suit(hearts):
            self.hearts.append(card)
            self.hearts.sort()
        elif card.suit == Suit(spades):
            self.spades.append(card)
            self.spades.sort()

    @property
    def hand(self) -> list[list[Card]]:
        # create hand of cards split up by suit
        return [self.clubs, self.diamonds, self.hearts, self.spades]

    def strToCard(self, card: str) -> Card:
        if len(card) == 0:
            return None
        
        offset = 1 if card[-1] == chr(65039) else 0

        suit = card[len(card)-1-offset:] # get the suit from the string

        try:
            suitIden = suits.index(suit)
        except:
            return None

        cardRank = card[0:len(card)-1-offset] # get rank from string

        try:
            cardRank = cardRank.upper()
        except AttributeError:
            pass

        # convert rank to int
        if cardRank == "J":
            cardRank = 11
        elif cardRank == "Q":
            cardRank = 12
        elif cardRank == "K":
            cardRank = 13
        elif cardRank == "A":
            cardRank = 14
        else:
            try:
                cardRank = int(cardRank)
            except ValueError:
                return None

        return Card(cardRank, suitIden)

    def containsCard(self, card: Union[Card, str]) -> bool:
        if(type(card) == str):
            card: Card = self.strToCard(card)

        for c in self.hand[card.suit.iden]:
            if c.rank.rank == card.rank.rank:
                return True
        return False

    def playCard(self, card: Union[Card, str]) -> Card:
        if(type(card) == str):
            card: Card = self.strToCard(card)

        if(self.containsCard(card)):
            self.removeCard(card)
            return card
        return None

    def removeCard(self, card: Union[Card, str]) -> None:
        if(type(card) == str):
            card = self.strToCard(card)
        
        suitId = card.suit.iden
        for c in self.hand[suitId]:
            if c == card:
                self.hand[card.suit.iden].remove(c)

    def __str__(self):
        handStr = ""
        for suit in self.hand:
            for card in suit:
                handStr += card.__str__() + " "
        return handStr
    
    def __iter__(self):
        for suit in self.hand:
            for card in suit:
                yield card