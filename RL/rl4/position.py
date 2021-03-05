from kivy.event import EventDispatcher
from kivy.properties import BoundedNumericProperty


class PositionBase:
    @property
    def x(self):
        """X axis"""
        cur_pos = self.pos_x
        state_centering = (cur_pos - self.unit + 1.0) % 1.0
        state = self.space_subdivisions * state_centering
        return int(round(state)) % self.space_subdivisions

    def increase_x(self, state_amount):
        """
        Increase the x axis by given (small) amount
        :param state_amount: double. amount to increase in the x axis
        :return:
        """
        pos_amount = state_amount / self.space_subdivisions
        self.pos_x = (self.pos_x + pos_amount) % 1.0

    @property
    def y(self):
        """Y axis"""
        cur_pos = self.pos_y
        state_centering = (cur_pos - self.unit + 1.0) % 1.0
        state = self.space_subdivisions * state_centering
        return int(round(state)) % self.space_subdivisions

    def increase_y(self, state_amount):
        """
        Increase the y axis by given (small) amount
        :param state_amount: double. amount to increase in the y axis
        :return:
        """
        pos_amount = state_amount / self.space_subdivisions
        if self.pos_y + pos_amount < self.unit:
            self.pos_y = self.unit
        elif self.pos_y + pos_amount > 1.0 - self.unit:
            self.pos_y = 1.0 - self.unit
        else:
            self.pos_y = self.pos_y + pos_amount

    def set_x(self, state_value):
        """
        Set the x axis decimal position
        :param state_value: decimal position in range [0, 1]
        :return:
        """
        val = state_value / self.space_subdivisions + self.unit
        epsilon = 1e-6
        if not self.unit <= val <= 1.0 - self.unit + epsilon:
            raise AttributeError("Value out of bounds")
        self.pos_x = val

    def set_y(self, state_value):
        """
        Set the y axis decimal position
        :param state_value: decimal position in range [0, 1]
        :return:
        """
        val = state_value / self.space_subdivisions + self.unit
        epsilon = 1e-6
        if not self.unit <= val <= 1.0 - self.unit + epsilon:
            raise AttributeError("Value out of bounds")
        self.pos_y = val

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        """Equivalent states in order to check fish and hooks in same position (caught fish)"""
        return self.x == other.x and self.y == other.y


class PositionGUI(EventDispatcher, PositionBase):
    """
    Position manager for fish, hooks, boat, etc. Enables a wrapped X axis and a bounded Y axis.
    """
    pos_x = BoundedNumericProperty(0, min=0, max=1)
    pos_y = BoundedNumericProperty(0, min=0, max=1)

    def __init__(self, parent, space_subdivisions):
        super().__init__()
        self.parent = parent
        self.space_subdivisions = space_subdivisions
        self.unit = 0.5 / self.space_subdivisions
        self.bind(pos_x=parent.on_state)
        self.bind(pos_y=parent.on_state)


class Position(PositionBase):
    """
    Position manager for fish, hooks, boat, etc. Enables a wrapped X axis and a bounded Y axis.
    """
    def __init__(self, parent, space_subdivisions):
        self.parent = parent
        self.space_subdivisions = space_subdivisions
        self.unit = 0.5 / self.space_subdivisions
        self.pos_x = 0
        self.pos_y = 0
