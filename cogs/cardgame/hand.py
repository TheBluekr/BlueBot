from random import randint
from .card import Card, Suit

clubs = 0
diamonds = 1
hearts = 2
spades = 3
suits = ["♣️", "♦️", "♥", "♠"]

class Hand:
    def __init__(self):

        self.clubs = []
        self.diamonds = []
        self.hearts = []
        self.spades = []

        # create hand of cards split up by suit
        self.hand = [self.clubs, self.diamonds, self.hearts, self.spades]

    def size(self):
        return len(self.clubs) + len(self.diamonds) + len(self.hearts) + len(self.spades)

    def addCard(self, card):
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

    def updateHand(self):
        self.hand = [self.clubs, self.diamonds, self.hearts, self.spades]

    def strToCard(self, card):
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

    def containsCard(self, cardRank, suitIden):
        for card in self.hand[suitIden]:
            if card.rank.rank == cardRank:
                cardToPlay = card

                # remove cardToPlay from hand
                self.hand[suitIden].remove(card)

                # update hand representation
                self.updateHand()
                return cardToPlay
        return None

    def playCard(self, card):
        card = self.strToCard(card)

        if card is None:
            return None
        else:
            cardRank, suitIden = card.rank, card.suit.iden

        # see if player has that card in hand
        return self.containsCard(cardRank, suitIden)

    def removeCard(self, card):
        if(type(card) == str):
            card = self.strToCard(card)
        
        suitId = card.suit.iden
        for c in self.hand[suitId]:
            if c == card:
                self.hand[card.suit.iden].remove(c)
                self.updateHand()

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