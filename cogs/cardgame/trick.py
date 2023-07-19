from .card import Card, InvalidCard, Suit, Rank

class Trick:
    def __init__(self, size=4, trump=-1):
        self.trick: list[Card] = [InvalidCard]*size
        self.suit: Suit = Suit(-1)
        self.trump: Suit = Suit(trump)
        self.highest: Rank = Rank(2) # rank of the high trump suit card in hand
        self.winner: int = -1

    @property
    def cards(self):
        return self.trick
    
    @property
    def size(self):
        count = 0
        card: Card
        for card in self.trick:
            if card.suit != Suit(-1):
                count += 1
        return count
    
    def getCard(self, index: int):
        return self.trick[index]

    def setTrickSuit(self, card):
        self.suit = card.suit

    def addCard(self, card: Card, index: int):
        if self.size == 0: # if this is the first card added, set the trick suit
            self.setTrickSuit(card)
            self.winner = index
        if card.suit == self.trump: # trump color always wins over suit
            self.setTrickSuit(card)

        self.trick[index] = card

        if card.suit == self.suit:
            if card.rank > self.highest:
                self.highest = card.rank
                self.winner = index

    def __iter__(self):
        for card in self.trick:
            yield card