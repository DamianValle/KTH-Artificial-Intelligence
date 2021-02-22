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


# FORWARD ALGORITHM

initial_alpha = f_multiply(init_prob_pi[0], f_get_col(obs_matrix_B, obs_seq[0]))


def forward(alpha, observation_sequence):
    if len(observation_sequence) == 0:
        print(round(sum(alpha), 6))
        return sum(alpha)
    first_term = [sum(f_multiply(alpha, f_get_col(trans_matrix_A, i))) for i in range(N)]
    current_alpha = f_multiply(first_term, f_get_col(obs_matrix_B, observation_sequence[0]))
    forward(current_alpha, observation_sequence[1:])


forward(initial_alpha, obs_seq[1:])
