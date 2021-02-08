from communicator import Communicator
from shared import SettingLoader


class Player:
    """
    Abstraction of a player. Can have or not a boat and achieves a score.
    """

    def __init__(self):
        self.score = 0
        self.boat = None
        self.fishes_density = {}
        self.fishes_cluster = {}


class PlayerController(SettingLoader, Communicator):
    def __init__(self):
        SettingLoader.__init__(self)
        Communicator.__init__(self)

    def player_loop(self):
        pass
