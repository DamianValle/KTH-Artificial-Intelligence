OBS_TO_MOVES = {
    0: (0, 1),
    1: (0, -1),
    2: (-1, 0),
    3: (1, 0),
    4: (-1, 1),
    5: (1, 1),
    6: (-1, -1),
    7: (1, -1)
}

MOVES_TO_OBS = {
    (0, 1): 0,
    (0, -1): 1,
    (-1, 0): 2,
    (1, 0): 3,
    (-1, 1): 4,
    (1, 1): 5,
    (-1, -1): 6,
    (1, -1): 7
}

ACT_TO_MOVES = {
    0: (0, 0),  # "stay"
    1: (0, 1),  # "up"
    2: (0, -1),  # "down"
    3: (-1, 0),  # "left"
    4: (1, 0)  # "right"
}

ACTION_TO_STR = {
    0: "stay",
    1: "up",
    2: "down",
    3: "left",
    4: "right"
}


class SettingLoader:
    """
    Mixin for including the settings object in controllers mainly
    """
    def __init__(self):
        self.settings = None

    def load_settings(self, settings):
        self.settings = settings
