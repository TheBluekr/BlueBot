from .card import Card, Suit

class Trick:
    def __init__(self, trump=-1):
        self.trick = [0, 0, 0]
        self.suit = Suit(-1)
        self.trump = Suit(trump)
        self.cardsInTrick = 0
        self.highest = 0 # rank of the high trump suit card in hand
        self.winner = -1

    def reset(self):
        self.trick = [0, 0, 0]
        self.suit = -1
        self.cardsInTrick = 0
        self.highest = 0
        self.winner = -1

    def cardsInTrick(self):
        count = 0
        for card in self.trick:
            if card is not 0:
                count += 1
        return count

    def setTrickSuit(self, card):
        self.suit = card.suit

    def addCard(self, card, index):
        if self.cardsInTrick == 0: # if this is the first card added, set the trick suit
            self.setTrickSuit(card)
        if card.suit == self.trump: # trump color always wins over suit
            self.setTrickSuit(card)

        self.trick[index] = card
        self.cardsInTrick += 1

        if card.suit == self.suit:
            if card.rank.rank > self.highest:
                self.highest = card.rank.rank
                self.winner = index