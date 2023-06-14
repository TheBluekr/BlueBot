from .hand import Hand
from .card import Card, Suit, Rank
from .trick import Trick

from typing import Union

class Player:
    def __init__(self, id: int):
        self.id: int = id
        self.hand: Hand = Hand()
        self.tricksWon: list = []
        self.points: int = 0

    def addCard(self, card: Card) -> None:
        self.hand.addCard(card)

    def play(self, c: Card) -> Union[Card, None]:
        card = self.hand.playCard(c)
        return card

    def trickWon(self, trick: Trick) -> None:
        self.tricksWon.append(trick)

    def hasSuit(self, suit: Suit) -> int:
        return len(self.hand.hand[suit.iden]) > 0

    def removeCard(self, card: Card) -> None:
        self.hand.removeCard(card)

    def discardTricks(self) -> None:
        self.tricksWon = []