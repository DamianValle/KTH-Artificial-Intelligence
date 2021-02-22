import math

from baum_welch_functions import f_create_matrix
from baum_welch_functions import f_alpha_pass
from baum_welch_functions import f_beta_pass
from baum_welch_functions import f_comp_gamma
from baum_welch_functions import f_re_estimate
from baum_welch_functions import f_prob_log

def main():
    l_input_file    = open("hmm4_01.in")
    l_matrices_list = l_input_file.read().splitlines()

    l_list_A    = l_matrices_list[0]
    l_list_B    = l_matrices_list[1]
    l_list_pi   = l_matrices_list[2]
    l_obs_seq   = l_matrices_list[3]

    l_trans_matrix_A    = f_create_matrix(l_list_A)
    l_obs_matrix_B      = f_create_matrix(l_list_B)
    l_init_prob_pi      = f_create_matrix(l_list_pi)

    l_obs_list  = list(l_obs_seq.split())
    l_obs_seq   = list(map(int, l_obs_list[1:]))

    # We are flipping the observation sequence because the Beta pass
    # operations are the same as the alpha pass operations
    # The output of Beta pass needs to be flipped so that the index will
    # correspond to the right time stamp
    
    l_M = len(set(l_obs_seq))           # Count of unique elements in obs seq 
    l_N = len(l_trans_matrix_A)
    l_T = len(l_obs_seq)

    l_iter_cnt      = 0
    l_max_iters     = 500
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

    for i in range(len(l_trans_matrix_A)):
        l_trans_matrix_A[i] = [round(num, 6) for num in l_trans_matrix_A[i]]
    #print("a_n: "  + str(l_trans_matrix_A))

    A = [item for sublist in l_trans_matrix_A for item in sublist]
    t_str_A = ' '.join([str(l_elem) for l_elem in A])
    print(l_N, l_N, t_str_A)
    
    for i in range(len(l_obs_matrix_B)):
        l_obs_matrix_B[i] = [round(num, 6) for num in l_obs_matrix_B[i]]
    #print("b_n: "  + str(l_obs_matrix_B))

    B = [item for sublist in l_obs_matrix_B for item in sublist]
    t_str_B = ' '.join([str(l_elem) for l_elem in B])
    print(l_N, l_M, t_str_B)

if __name__ == "__main__":
    main()
