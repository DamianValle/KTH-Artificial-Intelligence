def f_create_matrix(p_matrix_item):
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


def matrix_mul(a, b):
    mat1_r = len(a)
    mat2_c = len(b[0])
    result = [[0] * mat2_c] * mat1_r
    for i in range(mat1_r):
        # iterating by column by B
        for j in range(mat2_c):
            # iterating by rows of B
            for k in range(len(b)):
                result[i][j] += a[i][k] * b[k][j]
    return result


def main():
    a_ = [float(x) for x in input().split()]
    b_ = [float(x) for x in input().split()]
    pi_ = [float(x) for x in input().split()]

    trans_matrix = f_create_matrix(a_)
    obs_matrix = f_create_matrix(b_)
    init_prob = f_create_matrix(pi_)

    first_mul = matrix_mul(init_prob, trans_matrix)
    prob_dist = matrix_mul(first_mul, obs_matrix)
    for i in range(len(prob_dist[0])):
        prob_dist[0][i] = round(prob_dist[0][i], 3)

    probability = [item for sublist in prob_dist for item in sublist]
    t_str_prob = ' '.join([str(l_elem) for l_elem in probability])
    print(str(len(prob_dist)), str(len(prob_dist[0])), t_str_prob)

if __name__ == "__main__":
    main()