from .hand import Hand

class Player:
    def __init__(self, id):
        self.id = id
        self.hand = Hand()
        self.tricksWon = []
        self.points = 0

    def addCard(self, card):
        self.hand.addCard(card)

    def play(self, c=None):
        card = self.hand.playCard(c)
        return card

    def trickWon(self, trick):
        self.tricksWon.append(trick)

    def hasSuit(self, suit):
        return len(self.hand.hand[suit.iden]) > 0

    def removeCard(self, card):
        self.hand.removeCard(card)

    def discardTricks(self):
        self.tricksWon = []