'''
Suit identification (iden)
0: clubs
1: diamonds
2: hearts
3: spades
The suit that leads is trump, aces are high
'''

class Suit:
    def __init__(self, iden: int):
        self.iden: int = iden
        self.string: str = ""
        suits: list = ["♣️", "♦️", "♥", "♠"]
        if iden == -1:
            self.string = "Unset"
        elif iden <= 3:
            self.string = suits[iden]
        else:
            raise IndexError('Invalid card identifier')

    def __eq__(self, other):
        return self.iden == other.iden

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return self.iden < other.iden

    def __gt__(self, other):
        return self.iden > other.iden

    def __ge__(self, other):
        return not (self < other)

    def __le__(self, other):
        return not (self > other)

    def __str__(self):
        return self.string



'''
Ranks indicated by numbers 2-14, 2-Ace
Where ace is high and two is low
'''
class Rank:
    def __init__(self, rank: int):
        self.rank: int = rank
        self.string: str = ''

        strings = ["J", "Q", "K", "A"]

        if rank >= 2 and rank <= 10:
            self.string = str(rank)
        elif rank > 10 and rank <= 14:
            self.string = strings[rank - 11]
        else:
            raise IndexError('Invalid rank identifier')

    def __lt__(self, other):
        return self.rank < other.rank

    def __ge__(self, other):
        return not (self < other)

    def __gt__(self, other):
        return self.rank > other.rank

    def __le__(self, other):
        return not (self > other)

    def __eq__(self, other):
        return self.rank == other.rank

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return self.string

class Card:
    def __init__(self, rank: Rank, suit: Suit):
        self.rank: Rank = Rank(rank)
        self.suit: Suit = Suit(suit)

    def __lt__(self, other):
        return (self.rank < other.rank or (self.rank == other.rank and self.suit < other.suit))

    def __ge__(self, other):
        return not (self < other)

    def __gt__(self, other):
        return (self.rank > other.rank or (self.rank == other.rank and self.suit > other.suit))

    def __le__(self, other):
        return not (self > other)

    def __eq__(self, other):
        return self.rank == other.rank and self.suit == other.suit

    def __ne__(self, other):
        return not (self == other)

    def rank(self):
        return self.rank

    def suit(self):
        return self.suit

    def __str__(self):
        return self.rank.__str__() + self.suit.__str__()