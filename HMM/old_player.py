#!/usr/bin/env python3

from player_controller_hmm import PlayerControllerHMMAbstract
from constants import *
import random
import numpy as np
from calculate import calculate_temp
import sys
import math

epsilon = sys.float_info.epsilon
MAX_ITERS = 35

def calculate(model, n, m, emissions):
    A = model.A
    B = model.B
    initial_state = model.PI
    T = len(emissions)

    logprob = 0
    oldlogprob = -math.inf
    iters = 0

    while iters < MAX_ITERS and logprob > oldlogprob:
        ct = [0 for _ in range(T)]
        alpha = [[0 for _ in range(n)] for _ in range(T)]

        # compute \alpha_0(i)
        for i in range(n):
            alpha[0][i] = initial_state[0][i] * B[i][emissions[0]]
            ct[0] = ct[0] + alpha[0][i]

        # scale the \alpha_0(i)
        ct[0] = 1 / (ct[0] + epsilon)
        for i in range(n):
            alpha[0][i] = ct[0] * alpha[0][i]

        # compute \alpha_t(i)
        for t in range(1, T):
            for i in range(n):
                for j in range(n):
                    alpha[t][i] = alpha[t][i] + alpha[t - 1][j] * A[j][i]
                alpha[t][i] = alpha[t][i] * B[i][emissions[t]]
                ct[t] = ct[t] + alpha[t][i]

            # scale \alpha_t(i)
            ct[t] = 1 / (ct[t] + epsilon)
            for i in range(n):
                alpha[t][i] = ct[t] * alpha[t][i]

        # let \beta_{T-1}(i) = c_{T-1} for all i
        beta = [[ct[-1] for _ in range(n)] for _ in range(T)]

        # beta pass
        for t in reversed(range(T - 1)):
            for i in range(n):
                beta[t][i] = 0.0
                for j in range(n):
                    beta[t][i] = beta[t][i] + A[i][j] * B[j][emissions[t + 1]] * beta[t + 1][j]
                beta[t][i] = ct[t] * beta[t][i]

        # compute \gamma_t(i,j) and \gamma_t(i)
        gamma = [[0 for _ in range(n)] for _ in range(T)]
        gamma_ij = []

        for t in range(T - 1):
            gamma_aux = [[0 for _ in range(n)] for _ in range(n)]
            for i in range(n):
                for j in range(n):
                    gamma_aux[i][j] = alpha[t][i] * A[i][j] * B[j][emissions[t + 1]] * beta[t + 1][j]
                    gamma[t][i] = gamma[t][i] + gamma_aux[i][j]
            gamma_ij.append(gamma_aux)

        # special case for \gamma_{T-1}(i)
        for i in range(n):
            gamma[T - 1][i] = alpha[T - 1][i]

        # re-estimate A, B and PI

        # re-estimate PI
        initial_state = [gamma[0].copy()]

        # re-estimate A
        for i in range(n):
            denom = 0
            for t in range(T - 1):
                denom = denom + gamma[t][i]
            for j in range(n):
                numer = 0
                for t in range(T - 1):
                    numer = numer + gamma_ij[t][i][j]
                A[i][j] = numer / denom if denom != 0 else 0

        # re-estimate B
        for i in range(n):
            denom = 0
            for t in range(T):
                denom = denom + gamma[t][i]
            for j in range(m):
                numer = 0
                for t in range(T):
                    if emissions[t] == j:
                        numer = numer + gamma[t][i]
                B[i][j] = numer / denom if denom != 0 else 0

        # compute log(P(O|\lambda))
        logprob = 0
        for i in range(T):
            logprob += math.log(ct[i])
        logprob = -logprob

        # iterate or not iterate, that is the question
        iters += 1
        oldlogprob = logprob

    return A, B, initial_state

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
        #A, B, PI = calculate(self.models_fish[model_id], 1, N_EMISSIONS, self.obs)
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

        print(self.models_fish[0].A)

        if step < 10:      # 110 = 180 timesteps - 70 guesses
            return None
        else:
            fish_id, obs = self.fishes.pop()
            fish_type = 0
            max = 0
            for model, j in zip(self.models_fish, range(N_SPECIES)):
                m = forward_algorithm(obs, model)
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


        #if true_type not in self.seen_species:
        #    self.update_model(true_type)
        #    self.seen_species.add(true_type)
