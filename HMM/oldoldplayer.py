#!/usr/bin/env python3

from player_controller_hmm import PlayerControllerHMMAbstract
from constants import *
import random
import numpy as np
from calculate import calculate_temp
from baum_welch_functions import f_multiply, f_get_col
import math

def dot_prod(matrix_a, matrix_b):
    return [[a * b for a, b in zip(matrix_a[0], matrix_b)]]

def transpose(M):
    return [list(i) for i in zip(*M)]

def matrix_multiplication(A, B):
    return [[sum(a * b for a, b in zip(a_row, b_col)) for b_col in zip(*B)] for a_row in A]

def generate_row_stochastic(size):
    M = [(1 / size) + np.random.rand() / 1000 for _ in range(size)]
    s = sum(M)
    return [m / s for m in M]

def forward_algorithm(fish, model):
    obs = transpose(model.B)
    alpha = dot_prod(model.PI, obs[fish[0]])

    for e in fish[1:]:
        alpha = matrix_multiplication(alpha, model.A)
        alpha = dot_prod(alpha, obs[e])

    return sum(alpha[0])

def forward(alpha, observation_sequence, trans_matrix_A, obs_matrix_B):
    if len(observation_sequence) == 0:
        print(round(sum(alpha), 6))
        return sum(alpha)
    first_term = [sum(f_multiply(alpha, f_get_col(trans_matrix_A, i))) for i in range(N)]
    current_alpha = f_multiply(first_term, f_get_col(obs_matrix_B, observation_sequence[0]))
    forward(current_alpha, observation_sequence[1:], trans_matrix_A, obs_matri)


class Model:
    def __init__(self, species, emissions):
        self.PI = [generate_row_stochastic(species)]
        self.A = [generate_row_stochastic(species) for _ in range(species)]
        self.B = [generate_row_stochastic(emissions) for _ in range(species)]

    def set_A(self, A):
        self.A = A

    def set_B(self, B):
        self.B = B

    def set_PI(self, PI):
        self.PI = PI


class PlayerControllerHMM(PlayerControllerHMMAbstract):
    def init_parameters(self):
        """
        In this function you should initialize the parameters you will need,
        such as the initialization of models, or fishes, among others.
        """
        #self.seen_fishes = set()
        #self.seen_species = set()

        self.models_fish = [Model(1, N_EMISSIONS) for _ in range(N_SPECIES)]

        self.fishes = [(i, []) for i in range(N_FISH)]

    def update_model(self, model_id):
        A, B, PI = calculate_temp(self.models_fish[model_id].A, self.models_fish[model_id].B, self.models_fish[model_id].PI, self.obs)
        self.models_fish[model_id].set_A(A)
        self.models_fish[model_id].set_B(B)
        self.models_fish[model_id].set_PI(PI)

    def guess(self, step, observations):
        """
        This method gets called on every iteration, providing observations.
        Here the player should process and store this information,
        and optionally make a guess by returning a tuple containing the fish index and the guess.
        :param step: iteration number
        :param observations: a list of N_FISH observations, encoded as integers
        :return: None or a tuple (fish_id, fish_type)
        """

        for i in range(len(self.fishes)):
            self.fishes[i][1].append(observations[i])

        if step < 10:      # 110 = 180 timesteps - 70 guesses
            return None
        else:
            fish_id, obs = self.fishes.pop()
            fish_type = 0
            max = 0
            for model, j in zip(self.models_fish, range(N_SPECIES)):
                m = forward(alpha, obs, model.A, model.B)
                #print(m)
                #m = forward_algorithm(obs, model)
                #print(m)
                if m > max:
                    max = m
                    fish_type = j
            self.obs = obs ##????
            return fish_id, fish_type

    def reveal(self, correct, fish_id, true_type):
        """
        This methods gets called whenever a guess was made.
        It informs the player about the guess result
        and reveals the correct type of that fish.
        :param correct: tells if the guess was correct
        :param fish_id: fish's index
        :param true_type: the correct type of the fish
        :return:
        """

        if not correct:
            self.update_model(true_type)
