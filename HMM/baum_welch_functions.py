import math

def f_create_matrix(p_matrix_item):
    l_matrix_list   = list(p_matrix_item.split())
    l_matrix_elem   = list(map(float, l_matrix_list[2:]))
    l_rows          = int(l_matrix_list[0])
    l_cols          = int(l_matrix_list[1])
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
                    t_alpha += l_alpha_list[t - 1][j] * p_trans_matrix_A[j][i] * p_obs_matrix_B[i][p_obs_seq[t]]
                t_c += t_alpha
                t_alpha_list.append(t_alpha)
        # c_t_r is the reciprocal of t_c (c at time t)
        c_t_r = 1 / t_c
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
            trans_mat_temp_list.append(numer/denom)
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
            obs_mat_temp_list.append(numer / denom)
        obs_mat_new.append(obs_mat_temp_list)

    return [pi_temp_list], trans_mat_new, obs_mat_new


def f_prob_log(c, T):
    logprob = 0
    for i in range(T):
        logprob -= math.log(c[i])
    return logprob