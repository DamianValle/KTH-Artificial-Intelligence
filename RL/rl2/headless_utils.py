import numpy as np
import random
from position import Position
from shared import SettingLoader


class Fishes(SettingLoader):
    def __init__(self):
        super().__init__()
        self.seq_types_fishes = None
        self.fishderby = None
        self.fishes = {}

    def get_seq_types_fish(self):
        distribution = self.settings.num_fishes_per_type
        sequence = []
        for i, item in enumerate(distribution):
            sequence += [i] * item
        random.shuffle(sequence)
        self.seq_types_fishes = sequence
        return len(distribution)


class DiverModel:
    @staticmethod
    def diver_model(state2ind, space_subdivisions, prob_erratic=0.05):
        n_states = len(state2ind.keys())
        transition_matrix = np.zeros((n_states, 5, 5))
        for i in range(n_states):
            s = state2ind[i]
            for ai in range(5):
                mat = transition_matrix[i, ai]
                if s[0] < space_subdivisions - 1:
                    mat[1] = prob_erratic
                if s[0] > 0:
                    mat[0] = prob_erratic
                if s[1] < space_subdivisions - 1:
                    mat[3] = prob_erratic
                if s[1] > 0:
                    mat[2] = prob_erratic
                sum_p = np.sum(mat)
                if mat[ai] != 0.0:
                    mat[ai] = 1.0 - sum_p + prob_erratic
                elif sum_p > 0:
                    mat[:] /= sum_p

        possible_moves = np.zeros((n_states, 5))
        for i in range(n_states):
            pos = possible_moves[i]
            s = state2ind[i]
            if s[0] < space_subdivisions - 1:
                pos[1] = 1.0
            if s[0] > 0:
                pos[0] = 1.0
            if s[1] < space_subdivisions - 1:
                pos[3] = 1.0
            if s[1] > 0:
                pos[2] = 1.0
            pos[4] = 1.0
        return possible_moves, transition_matrix


class Diver:
    has_fish = None

    def __init__(self, init_state, space_subdivisions, states, stoch=True):
        self.position = Position(self, space_subdivisions)
        self.position.set_x(init_state[0])
        self.position.set_y(init_state[1])
        self.model, self.transition_matrix = DiverModel().diver_model(
            states, space_subdivisions, prob_erratic=0.05 if stoch else 0.0)


class Fish:
    def __init__(self, init_state, type_fish, name, settings, score=0):
        self.orientation = 1.0
        self.caught = None
        self.type_fish = type_fish
        self.name = name
        self.prev_direction = random.choice(range(8))
        if self.prev_direction in [2, 4, 6]:
            self.orientation = -1
        self.observation = None
        self.updates_cnt = 0
        self.settings = settings
        space_subdivisions = 10
        self.position = Position(self, space_subdivisions)
        self.position.set_x(init_state[0])
        self.position.set_y(init_state[1])
        self.prev_move = None
        self.score = score


class JellySmile:
    def __init__(self, position=None, space_subdivisions=None, score=0):
        self.position = Position(self, space_subdivisions)
        self.position.set_x(position[0])
        self.position.set_y(position[1])
        self.score = score
        self.touched = False


class Player:
    """
    Abstraction of a player. Can have or not a boat and achieves a score.
    """
    def __init__(self):
        self.score = 0
        self.diver = None
        self.diver_headless = None
        self.fishes_density = {}
        self.fishes_cluster = {}


class PrintScoresAbstract:
    def __init__(self):
        self.time = 0
        self.total_time = 0
        self.fishderby = None
        self.players = {}

    def print_score(self):
        raise NotImplementedError


class PrintScore2Players(PrintScoresAbstract):
    def print_score(self):
        print("Elapsed time:",
              str(self.time) + '/' + str(self.total_time), "s\tScore:",
              self.players[0].score - self.players[1].score)


class PrintScore1Player(PrintScoresAbstract):
    def print_score(self):
        print("Elapsed time:",
              str(self.time) + '/' + str(self.total_time), "s\tScore:",
              self.player.score)