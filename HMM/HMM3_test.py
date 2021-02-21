import math

def create_matrix(n_rows, n_col, data_list):
    mat = []
    for i in range(n_rows):
        row_list = []
        for j in range(n_col):
            if data_list[j] not in mat:
                row_list.append(data_list[n_col * i + j])
        mat.append(row_list)
    return mat

input_file = open("hmm4_01.in")
matrices_list = input_file.read().splitlines()
#print(matrices_list)

first_matrix = matrices_list[0]
second_matrix = matrices_list[1]
third_matrix = matrices_list[2]
obs_seq = matrices_list[3]

# Creating the State transition matrix A
lst_1 = list(first_matrix.split())
A_rows = int(lst_1[0])
A_col = int(lst_1[1])
a_str = lst_1[2:]
A = list(map(float, a_str))  # Transition matrix
#print(A)

# Creating the Emission matrix B
lst_2 = list(second_matrix.split())
B_rows = int(lst_1[0])
B_col = int(lst_1[1])
b_str = lst_2[2:]
B = list(map(float, b_str))  # Emission matrix
#print(B)

# Creating the Initial state distribution matrix pi
lst_3 = list(third_matrix.split())
pi_str = lst_3[2:]
pi = list(map(float, pi_str))  # Initial probabilities
#print(pi)
pi_col = len(pi)

# Extracting the observation sequence
lst_4 = list(obs_seq.split())
obs_str = lst_4[1:]
obs_seq = list(map(int, obs_str))  # Observation sequence
M = len(set(obs_seq))
#print("M: " + str(M))
#print(obs_seq)

# We are flipping the observation sequence so that code can be reused
# The output of Beta pass needs to be flipped so that the index will
# correspond to the right time stamp
seq_beta = obs_seq[::-1]
#print("seq_beta: " + str(seq_beta))

# Main
trans_matrix_A = create_matrix(A_rows, A_col, A)
obs_matrix_B = create_matrix(B_rows, B_col, B)
init_prob_pi = create_matrix(1, pi_col, pi)
print(init_prob_pi)

N = len(trans_matrix_A[0])
T = len(obs_seq)
oldlogprob = float("-inf")
iters = 0
max_iters = 500
log_probab = 0


def alpha_pass(a, b, p, seq):
    alpha_list = []
    N = len(a[0])
    T = len(seq)
    c = []
    for t in range(T):
        ##print(t)
        c_t = 0
        alpha_temp_list = []
        for i in range(N):
            b_temp = b[i]
            if t == 0:
                pi_temp = p[0]
                ##print(pi_temp)
                alpha = pi_temp[i] * b_temp[seq[t]]
                ##print(alpha)
                c_t += alpha
                alpha_temp_list.append(alpha)
                ##print("alpha_temp_list: " + str(alpha_temp_list))
            else:
                alpha_calc_list = alpha_list[t - 1]
                ##print(alpha_calc_list)
                alpha = 0
                for j in range(N):
                    trans_temp = a[j]
                    alpha += alpha_calc_list[j] * trans_temp[i] * b_temp[seq[t]]
                    # #print("sum_term: " + str(sum_term))
                c_t += alpha
                alpha_temp_list.append(alpha)
                ##print(alpha_temp_list)

        # c_t_r is the reciprocal of c_t (c at time t)
        c_t_r = 1 / c_t #c_t_r = round(1 / c_t, 6)
        ##print("c at time t:" + str(c_t_r))
        for m in range(N):
            alpha_temp_list[m] = c_t_r * alpha_temp_list[m] #alpha_temp_list[m] = round(c_t_r * alpha_temp_list[m], 6)
        ##print("alpha_temp_list: " + str(alpha_temp_list))
        c.append(c_t_r)

        alpha_list.append(alpha_temp_list)
        ##print("alpha_list: " + str(alpha_list))

    return alpha_list, c


def beta_pass(a, b, p, seq, c):
    beta_list = []
    N = len(a[0])
    T = len(seq)
    for t in range(T):
        ##print(t)
        beta_temp_list = []
        for i in range(N):     # to state
            trans_temp = a[i]
            if t == 0:
                pi_temp = p[0]
                ##print(pi_temp)
                beta = c[t]
                #print(beta)
                beta_temp_list.append(beta)
            else:
                sum_term = 0
                beta_calc_list = beta_list[t-1]
                for j in range(N):     # from state
                    b_temp = b[j]
                    sum_term += beta_calc_list[j] * trans_temp[j] * b_temp[seq[t]]
                    # #print("sum_term: " + str(sum_term))
                beta_temp_list.append(sum_term)
                ##print(beta_temp_list)

        ##print("beta_temp_list: " + str(beta_temp_list))
        if t > 0:
            for m in range(N):
                beta_temp_list[m] = c[t] * beta_temp_list[m] #beta_temp_list[m] = round(c[t] * beta_temp_list[m], 6)
            ##print("beta_list: " + str(beta_temp_list))

        beta_list.append(beta_temp_list)
        ##print("beta_list: " + str(beta_list))

    return beta_list


def di_gamma(a, b, seq, alpha_list, beta_list):
    N = len(a[0])
    T = len(seq)
    gama_list = []
    gama_ij_list = []
    t = 0
    for t in range(T-1):
        ##print(t)
        gama_temp_list = []
        gama_ij_temp_list = []
        alpha_t = alpha_list[t]
        beta_t1 = beta_list[t + 1]
        for i in range(N):
            a_temp = a[i]
            gama_val_temp = []
            gama = 0
            for j in range(N):
                b_temp = b[i]
                gama_ij = alpha_t[i] * a_temp[j] * b_temp[seq[t+1]] * beta_t1[j]
                gama += gama_ij
                gama_val_temp.append(gama_ij) #gama_val_temp.append(round(gama_ij, 6))
            gama_temp_list.append(gama) #gama_temp_list.append(round(gama, 6))
            gama_ij_temp_list.append(gama_val_temp)

        gama_list.append(gama_temp_list)
        ##print("gama_list: " + str(gama_list))

        gama_ij_list.append(gama_ij_temp_list)
        ##print("gama_ij_list: " + str(gama_ij_list))

    # #print("t outside t loop: " + str(t))
    ##print(t+1)
    gama_temp_list = []
    alpha_temp_list = alpha_list[t+1]
    for k in range(N):
        gama_temp_list.append(alpha_temp_list[k])
    gama_list.append(gama_temp_list)
    #print("gama_list: " + str(gama_list))

    return gama_list, gama_ij_list


def re_estimate(gama_list, gama_ij_list, seq):
    # Re-estimate value of pi
    pi_temp_list = []
    gamma_zero_temp = gama_list[0]
    for i in range(N):
        pi_new = gamma_zero_temp[i]
        ##print("pi_new: " + str(pi_new))
        pi_temp_list.append(pi_new)
    #print("pi_temp_list: " + str(pi_temp_list))

    # Re-estimating transition matrix A
    trans_mat_new = []
    for i in range(N): #rows
        denom = 0
        trans_mat_temp_list = []
        for t in range(T-1):
            gamma_list_t = gama_list[t]
            denom += gamma_list_t[i]
        for j in range(N): #COLS
            numer = 0
            for t in range(T-1):
                gamma_ij_list_t = gama_ij_list[t]
                gama_temp = gamma_ij_list_t[j] #gama_temp_i = gamma_ij_list_t[i]
                numer += gama_temp[i] #numer += gama_temp_i[j]
            trans_mat_temp_list.append(numer/denom)
        trans_mat_new.append(trans_mat_temp_list)
        #print("trans_mat_new: " + str(trans_mat_new))
    #print("trans_mat_new: " + str(trans_mat_new))

    # Re-estimating transition matrix B
    obs_mat_new = []
    for i in range(N):  # rows
        denom = 0
        obs_mat_temp_list = []
        for t in range(T):
            gamma_list_t = gama_list[t]
            denom += gamma_list_t[i]
        for j in range(M):  # COLS
            numer = 0
            for t in range(T):
                gamma_list_t = gama_list[t]
                if seq[t] == j:
                    numer += gamma_list_t[i]
            obs_mat_temp_list.append(numer / denom)
        obs_mat_new.append(obs_mat_temp_list)
        #print("obs_mat_new: " + str(obs_mat_new))
    #print("obs_mat_new: " + str(obs_mat_new))

    return [pi_temp_list], trans_mat_new, obs_mat_new


def prob_log(c):
    logprob = 0
    for i in range(T):
        logprob += math.log(c[i])
    logprob = -logprob
    return logprob


alpha_final, c_val = alpha_pass(trans_matrix_A, obs_matrix_B, init_prob_pi, obs_seq)
#print("alpha_final: " + str(alpha_final))
#print("list of C at end of alpha pass: " + str(c_val))

# Flipping C for the beta pass
c_beta = c_val[::-1]

beta_flip = beta_pass(trans_matrix_A, obs_matrix_B, init_prob_pi, seq_beta, c_beta)
beta_final = beta_flip[::-1]
#print("beta_final: " + str(beta_final))

gamma_list, gamma_ij_list = di_gamma(trans_matrix_A, obs_matrix_B, obs_seq, alpha_final, beta_final)
#print("gama_list: " + str(gamma_list))
#print("gama_ij_list: " + str(gamma_ij_list))

pi_n, a_n, b_n = re_estimate(gamma_list, gamma_ij_list, obs_seq)
#print("pi_n: " + str(pi_n))
#print("a_n: " + str(a_n))
#print("b_n: " + str(b_n))

log_probability = prob_log(c_val)
#print("log_probability: " + str(log_probability))'''


while iters < max_iters:
    print("Iteration count : ", str(iters))
    if log_probability > oldlogprob:
        oldlogprob = log_probability

        alpha_final, c_val = alpha_pass(a_n, b_n, pi_n, obs_seq)

        c_beta      = c_val[::-1]
        beta_flip   = beta_pass(a_n, b_n, pi_n, seq_beta, c_beta)
        beta_final  = beta_flip[::-1]

        gamma_list, gamma_ij_list = di_gamma(a_n, b_n, obs_seq, alpha_final, beta_final)

        pi_n, a_n, b_n = re_estimate(gamma_list, gamma_ij_list, obs_seq)

        log_probability = prob_log(c_val)
    else:
        break
    iters += 1

print("pi_n: " + str(pi_n))
print("a_n: " + str(a_n))
print("b_n: " + str(b_n))


