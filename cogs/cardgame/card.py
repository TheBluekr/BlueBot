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


clubs = 0
diamonds = 1
hearts = 2
spades = 3
suits = ["♣️", "♦️", "♥", "♠"]

class Card:
    def __init__(self, rank: Rank, suit: Suit):
        self.rank: Rank = Rank(rank)
        self.suit: Suit = Suit(suit)
    
    @classmethod
    def fromString(cls, card: str):
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

        return cls(cardRank, suitIden)

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
        if(self.suit.iden == -1):
            return "None"
        return self.rank.__str__() + self.suit.__str__()

InvalidCard = Card(2, -1)