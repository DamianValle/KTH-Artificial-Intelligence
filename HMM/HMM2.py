def f_create_matrix(p_matrix_item):
    # l_matrix_list   = list(p_matrix_item.split())
    l_matrix_elem = list(map(float, p_matrix_item[2:]))
    l_rows = int(p_matrix_item[0])
    l_cols = int(p_matrix_item[1])
    l_matrix = []
    for i_row in range(l_rows):
        t_row_list = []
        for i_col in range(l_cols):
            if l_matrix_elem[i_col] not in l_matrix:
                t_row_list.append(l_matrix_elem[l_cols * i_row + i_col])
        l_matrix.append(t_row_list)
    return l_matrix


def f_multiply(A, B):
    return [i * j for i, j in zip(A, B)]


def f_get_col(matrix, col):
    return [row[col] for row in matrix]


a_ = [float(x) for x in input().split()]
b_ = [float(x) for x in input().split()]
pi_ = [float(x) for x in input().split()]
os_ = [int(x) for x in input().split()]

trans_matrix_A = f_create_matrix(a_)
obs_matrix_B = f_create_matrix(b_)
init_prob_pi = f_create_matrix(pi_)
obs_seq = os_[1:]

N = len(trans_matrix_A[0])
T = len(obs_seq)


def viterbi(delta, delta_idx, observation_seq):
    """
    delta : probabilities
    delta_idx : states
    all_probabilities :
    [[0.0, 0.0, 0.0, 0.0], [0.07200000000000002, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]]
    """

    if len(observation_seq) == 0:
        # backtrack
        state_sequence = []

        last_state = delta.index(max(delta))
        state_sequence.append(last_state)
        for i in range(len(delta_idx) - 1, 0, -1):
            state_sequence.insert(0, delta_idx[i][last_state])
            last_state = delta_idx[i][last_state]

        print(' '.join([str(x) for x in state_sequence]))
        return

    # implementing max_j∈[1,..N] a_j,i * δt−1(j) * b_i(ot)
    all_probabilities = [
        [delta[prev_st] * trans_matrix_A[prev_st][curr_st] * obs_matrix_B[curr_st][observation_seq[0]] for prev_st in range(N)] for
        curr_st in range(N)]
    max_probability = [max(probabilities_curr_st) for probabilities_curr_st in all_probabilities]
    # In order to be able to trace back the most likely sequence later on, it is convenient to store the indices
    # of the most likely states at each step.
    delta_idx.append(
        [probabilities_curr_st.index(max_probability[i]) for i, probabilities_curr_st in enumerate(all_probabilities)])

    viterbi(max_probability, delta_idx, observation_seq[1:])


initial_delta = f_multiply(init_prob_pi[0], f_get_col(obs_matrix_B, obs_seq[0]))
initial_delta_idx = [[None] * N]

# Implement Viterbi algorithm
viterbi(initial_delta, initial_delta_idx, obs_seq[1:])
