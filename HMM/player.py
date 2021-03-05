#!/usr/bin/env python3

from player_controller_hmm import PlayerControllerHMMAbstract
from constants import *
import random
import numpy as np
import sys


epsilon = sys.float_info.epsilon

def calculate_temp(l_trans_matrix_A, l_obs_matrix_B, l_init_prob_pi, l_obs_seq):

    # We are flipping the observation sequence because the Beta pass
    # operations are the same as the alpha pass operations
    # The output of Beta pass needs to be flipped so that the index will
    # correspond to the right time stamp
    
    #l_M = len(set(l_obs_seq))           # Count of unique elements in obs seq 
    l_M = len(l_obs_seq)
    l_N = len(l_trans_matrix_A)
    l_T = len(l_obs_seq)

    l_iter_cnt      = 0
    l_max_iters     = 5
    l_old_log_prob  = float("-inf")
    l_log_prob      = 1

    while l_iter_cnt < l_max_iters and l_log_prob > l_old_log_prob:
        l_iter_cnt += 1
        #print("Iteration count : ", str(l_iter_cnt))
        if l_iter_cnt != 1:
            l_old_log_prob = l_log_prob
            
        l_alpha_vals, l_c_val = f_alpha_pass(l_trans_matrix_A, l_obs_matrix_B, l_init_prob_pi, l_obs_seq, l_N, l_T)
        
        l_c_beta    = l_c_val[::-1]
        l_seq_beta  = l_obs_seq[::-1]
        l_beta_flip = f_beta_pass(l_trans_matrix_A, l_obs_matrix_B, l_init_prob_pi, l_seq_beta, l_c_beta, l_N, l_T)
        l_beta_vals = l_beta_flip[::-1]

        l_gamma_list, l_gamma_ij_list = f_comp_gamma(l_trans_matrix_A, l_obs_matrix_B, l_obs_seq, l_alpha_vals, l_beta_vals, l_N, l_T)

        l_init_prob_pi, l_trans_matrix_A, l_obs_matrix_B = f_re_estimate(l_gamma_list, l_gamma_ij_list, l_obs_seq, l_M, l_N, l_T)

        l_log_prob = f_prob_log(l_c_val, l_T) 

    return l_trans_matrix_A, l_obs_matrix_B, l_init_prob_pi


def f_create_matrix(p_matrix_item):
    #l_matrix_list   = list(p_matrix_item.split())
    l_matrix_elem   = list(map(float, p_matrix_item[2:]))
    l_rows          = int(p_matrix_item[0])
    l_cols          = int(p_matrix_item[1])
    l_matrix        = []
    for i_row in range(l_rows):
        t_row_list = []
        for i_col in range(l_cols):
            if l_matrix_elem[i_col] not in l_matrix:
                t_row_list.append(l_matrix_elem[l_cols * i_row + i_col])
        l_matrix.append(t_row_list)
    return l_matrix


def f_alpha_pass(p_trans_matrix_A, p_obs_matrix_B, p_init_prob_pi, p_obs_seq, p_N, p_T):
    l_alpha_list = []
    l_c = []
    for t in range(p_T):
        t_c = 0
        t_alpha_list = []
        t_pi = p_init_prob_pi[0]
        for i in range(p_N):
            if t == 0:
                t_alpha = t_pi[i] * p_obs_matrix_B[i][p_obs_seq[t]]
                t_c += t_alpha
                t_alpha_list.append(t_alpha)
            else:
                t_alpha = 0
                for j in range(p_N):
                    #print("len l_alpha_list: ", len(l_alpha_list))
                    t_alpha += l_alpha_list[t - 1][j] * p_trans_matrix_A[j][i] * p_obs_matrix_B[i][p_obs_seq[t]]
                t_c += t_alpha
                t_alpha_list.append(t_alpha)
        # c_t_r is the reciprocal of t_c (c at time t)
        c_t_r = 1 / (t_c + epsilon)
        for m in range(p_N):
            t_alpha_list[m] = c_t_r * t_alpha_list[m]
        l_c.append(c_t_r)
        l_alpha_list.append(t_alpha_list)

    return l_alpha_list, l_c


def f_beta_pass(a, b, p, seq, c, N, T):
    beta_list = []
    pi_temp = p[0]
    for t in range(T):
        beta_temp_list = []
        for i in range(N):     # to state
            if t == 0:
                beta = c[t]
                beta_temp_list.append(beta)
            else:
                sum_term = 0
                for j in range(N):     # from state
                    sum_term += beta_list[t-1][j] * a[i][j] * b[j][seq[t-1]]
                beta_temp_list.append(sum_term)
        if t > 0:
            for m in range(N):
                beta_temp_list[m] = c[t] * beta_temp_list[m]
        beta_list.append(beta_temp_list)

    return beta_list
    
    
def f_comp_gamma(a, b, seq, alpha_list, beta_list, N, T):
    gama_list = []
    gama_ij_list = []
    for t in range(T-1):
        gama_temp_list = []
        gama_ij_temp_list = []
        for i in range(N):
            gama_val_temp = []
            gama = 0
            for j in range(N):
                gama_ij = alpha_list[t][i] * a[i][j] * b[j][seq[t+1]] * beta_list[t + 1][j]
                gama += gama_ij
                gama_val_temp.append(gama_ij)
            gama_temp_list.append(gama)
            gama_ij_temp_list.append(gama_val_temp)
        gama_list.append(gama_temp_list)
        gama_ij_list.append(gama_ij_temp_list)
    gama_temp_list = []
    alpha_temp_list = alpha_list[t+1]
    for k in range(N):
        gama_temp_list.append(alpha_temp_list[k])
    gama_list.append(gama_temp_list)
    return gama_list, gama_ij_list


def f_re_estimate(gama_list, gama_ij_list, seq, M, N, T):
    # Re-estimate value of pi
    pi_temp_list = []
    for i in range(N):
        pi_temp_list.append(gama_list[0][i])

    # Re-estimating transition matrix A
    trans_mat_new = []
    for i in range(N):
        denom = 0
        trans_mat_temp_list = []
        for t in range(T-1):
            denom += gama_list[t][i]
        for j in range(N):
            numer = 0
            for t in range(T-1):
                gama_temp_i = gama_ij_list[t][i]
                numer += gama_temp_i[j]
            trans_mat_temp_list.append(numer/(denom + epsilon))
        trans_mat_new.append(trans_mat_temp_list)

    # Re-estimating transition matrix B
    obs_mat_new = []
    for i in range(N):
        denom = 0
        obs_mat_temp_list = []
        for t in range(T):
            denom += gama_list[t][i]
        for j in range(M):
            numer = 0
            for t in range(T):
                if seq[t] == j:
                    numer += gama_list[t][i]
            obs_mat_temp_list.append(numer / (denom + epsilon))
        obs_mat_new.append(obs_mat_temp_list)

    return [pi_temp_list], trans_mat_new, obs_mat_new


def f_prob_log(c, T):
    logprob = 0
    for i in range(T):
        logprob -= np.log(c[i])
    return logprob

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

        if step < 110:      # 110 = 180 timesteps - 70 guesses
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
            self.obs = obs
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