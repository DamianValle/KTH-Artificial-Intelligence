#import math

from baum_welch_functions import f_alpha_pass
from baum_welch_functions import f_beta_pass
from baum_welch_functions import f_comp_gamma
from baum_welch_functions import f_re_estimate
from baum_welch_functions import f_prob_log

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
    l_max_iters     = 50
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
