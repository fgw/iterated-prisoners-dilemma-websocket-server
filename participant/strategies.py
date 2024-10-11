import random


class Strategy:
    def __init__(self):
        pass

    def play(self, state):
        pass


class NaiveStrategy(Strategy):
    """
    Always collaborate
    """
    def play(self, state):
        return "C"


class TitForTatStrategy(Strategy):
    """
    Copy the last choice of the opponent
    """
    def play(self, state):
        choice = state
        if choice not in ("C", "B"):
            choice = "C"
        return choice


class RandomStrategy(Strategy):
    """
    Choose a random action
    """
    def play(self, state):
        return random.choice(("C", "B"))
