import random as rand

from .card import Card

numSuits = 4
minRank = 2
maxRank = 15

class Deck:
    def __init__(self):
        self.deck: list[Card] = []
        for suit in range(0, numSuits):
            for rank in range(minRank, maxRank):
                self.deck.append(Card(rank, suit))
    
    def clear(self):
        self.deck: list[Card] = []

    def __str__(self) -> str:
        deckStr = ''
        for card in self.deck:
            deckStr += card.__str__() + '\n'
        return deckStr

    def shuffle(self):
        rand.shuffle(self.deck)

    def deal(self) -> Card:
        return self.deck.pop(0)

    def sort(self):
        self.deck.sort()

    @property
    def size(self) -> int:
        return len(self.deck)

    def addCard(self, card: Card):
        self.deck.append(card)

    def addCards(self, cards: list[Card]) -> None:
        self.deck += cards