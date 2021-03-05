import numpy as np


# import matplotlib.pyplot as plt

def initialize_transitions(transitions):
    if transitions is not None:
        return transitions

    N = HiddenMarkovModel.STATES
    sigma = HiddenMarkovModel.SIGMA
    transitions = np.ones((N, N)) * 1 / N + np.abs(np.random.randn(N, N) * sigma)
    row_sums = transitions.sum(axis=1)
    transitions = transitions / row_sums[:, np.newaxis]

    return transitions


def initialize_emissions(emissions):
    if emissions is not None:
        return emissions

    N, M = HiddenMarkovModel.STATES, HiddenMarkovModel.EMISSIONS
    sigma = HiddenMarkovModel.SIGMA
    emissions = np.ones((N, M)) * 1 / M + np.abs(np.random.randn(N, M) * sigma)

    row_sums = emissions.sum(axis=1)
    emissions = emissions / row_sums[:, np.newaxis]

    return emissions


def initialize_distribution(distribution):
    if distribution is not None:
        return distribution
    N = HiddenMarkovModel.STATES
    sigma = HiddenMarkovModel.SIGMA
    distribution = np.ones(N) * 1 / N + np.abs(np.random.randn(N) * sigma)
    row_sums = distribution.sum(axis=0)
    distribution = distribution / row_sums[np.newaxis]

    return distribution


class Fish:

    def __init__(self):
        self.CLASS = None
        self.logprob = -np.inf
        self.sequence = []
        self.revealed = False


class HiddenMarkovModel(object):
    STATES = 8
    EMISSIONS = 8
    SIGMA = 1e-2

    def __init__(self, transitions=None, emissions=None, distribution=None):
        self.transitions = initialize_transitions(transitions)
        self.emissions = initialize_emissions(emissions)
        self.distribution = initialize_distribution(distribution)

    def predict_next_emission_distribution(self, observations):
        """
        Predict the next emission distribution based on
        observations :param(observations)
        :param observations: the observations of the fish
        :return the next emission distribution vector
        """
        viterbi = Viterbi()
        viterbi.run(
            self.transitions,
            self.emissions,
            self.distribution,
            observations
        )

        current_state_index = viterbi.indices[-1]

        distribution = np.zeros(HiddenMarkovModel.STATES)
        distribution[current_state_index] = 1.

        transition_distribution = np.dot(
            self.transitions,
            distribution
        )

        next_emission_distribution = np.dot(
            self.emissions,
            transition_distribution,
        )

        return next_emission_distribution

    def train(self, observations, iterations, model):
        """
        Train the hidden markov model using the forward backward algorithm.
        The model will be re-estimated until convergance
        or iterations :param(iterations) is reached
        :param model: model to train with new observations
        :param observations: the observations generated
        :param iterations: the number of maximum iterations
        """
        c = np.zeros(len(observations))
        old_log_prob = -float("inf")
        # l = []
        for iteration in range(iterations):
            alpha, c = self.forward_pass(observations, c, model.transitions, model.emissions,
                                         model.distribution)
            beta = self.backward_pass(observations, c, model.transitions, model.emissions)
            gamma, di_gamma = self.compute_di_gammas(observations, alpha, beta)

            model = self.reestimate(observations, gamma, di_gamma)

            with np.errstate(divide="raise"):
                log_prob = -np.sum(np.log(c[:]))

            # l += [log_prob]
            if log_prob - old_log_prob < 0.1:  # log_prob < old_log_prob:
                break

            old_log_prob = log_prob

        return old_log_prob, model

    def reestimate(self, observations, gamma, di_gamma):
        """
        Re-estimates the model parameters to best fit the observations
        """
        N = self.transitions.shape[0]
        model = HiddenMarkovModel()
        A, B, pi = np.zeros(self.transitions.shape), np.zeros(self.emissions.shape), np.zeros(self.distribution.shape)

        for i in range(N):
            pi[i] = self.reestimate_distribution(gamma, i)
            A = self.reestimate_transitions(observations, gamma, di_gamma, i, A)
            B = self.reestimate_emissions(observations, gamma, i, B)
        model.distribution = pi
        model.transitions = A
        model.emissions = B
        return model

    def reestimate_distribution(self, gamma, i):
        """
        Re-estimates the model's distribution vector based on the gamma values
        """
        # self.distribution[i] = gamma[0, i]
        return gamma[0, i]

    def reestimate_transitions(self, observations, gamma, di_gamma, i, A):
        """
        Re-estimate transition matirx using gamma
        and di gamma values and scaling matrix after
        computations.
        :param observations: numpy array of observations
        :param gamma: numpy array of gamma values
        :param di_gamma: numpy array of di gamma values
        :param i: current iteration
        """
        N = self.transitions.shape[0]
        T = observations.shape[0]

        for j in range(N):
            A[i][j] = 0.

            numer = 0.000000
            denom = 0.000000

            for t in range(T - 1):
                numer += di_gamma[t][i][j]
                denom += gamma[t][i]

            A[i][j] = 0.

            if denom != 0.:
                A[i][j] = numer / denom

            if A[i][j] == 0.:
                A[i][j] = 1e-16

        A[i, :] /= A[i, :].sum()
        return A

    def reestimate_emissions(self, observations, gamma, i, B):
        """
        Re-estimate emission matrix using gamma values
        and scaling matrix after computations.
        :param observations: numpy array of observations
        :param gamma: numpy array of gamma values
        :param i: current iteration
        """
        N = self.emissions.shape[1]
        T = observations.shape[0]

        for j in range(N):
            numer = 0.000000
            denom = 0.000000

            for t in range(T - 1):
                if observations[t] == j:
                    numer += gamma[t][i]
                denom += gamma[t][i]

            B[i][j] = 0.

            if denom != 0.:
                B[i][j] = numer / denom

            if B[i][j] == 0.:
                B[i][j] = 1e-16

        # B /= B.sum(axis=1)[:, np.newaxis]
        B[i, :] /= B[i, :].sum()

        return B

    def forward_pass(self, observations, factors, A, B, pi):
        """
        Forward pass algorithm
        :param observations: numpy array of observations
        :param factors: factors used for scaling the numbers
        :return: matrix with alpha values
        """

        N = self.transitions.shape[0]
        T = observations.shape[0]

        alpha = np.zeros((T, N))

        for i in range(N):
            alpha[0][i] = pi[i] * B[i][observations[0]]
            factors[0] += alpha[0][i]

        self.scale(alpha, factors, 0)

        for t in range(1, observations.shape[0]):
            self.__forward_pass(alpha, observations, factors, t, A, B)
            self.scale(alpha, factors, t)

        return alpha, factors

    def backward_pass(self, observations, factors, A, B):
        """
        Backward pass algorithm

        :param observations: numpy array of observations
        :param factors: factors used for scaling the numbers
        :return matrix with beta values
        """

        N = self.transitions.shape[0]
        T = observations.shape[0]

        beta = np.zeros((T, N))

        for i in range(N):
            beta[T - 1][i] = factors[T - 1]

        for t in range(T - 2, -1, -1):
            self.__backward_pass(beta, observations[t + 1], factors, t, A, B)

        return beta

    def compute_di_gammas(self, observations, alpha, beta):
        """
        Compute di_gammas needed for re-estimating the model parameters

        :param observations: numpy array of observations
        :param alpha: numpy array of alpha values
        :param beta: numpy array of beta values
        """

        N = self.transitions.shape[0]
        T = observations.shape[0]

        gamma = np.zeros((T, N))
        di_gamma = np.zeros((T, N, N))

        for t in range(T - 1):
            self.__compute_di_gammas(gamma, di_gamma, observations[t + 1], alpha, beta, t)

        return gamma, di_gamma

    def __compute_di_gammas(self, gamma, di_gamma, observation, alpha, beta, t):
        """
        Compute di_gammas for time step t
        """
        denom = 0.
        N = self.transitions.shape[0]

        for i in range(N):
            for j in range(N):
                denom += alpha[t][i] * \
                         self.transitions[i][j] * \
                         self.emissions[j][observation] * \
                         beta[t + 1][j]

        for i in range(N):

            gamma[t][i] = 0.

            for j in range(N):

                if denom != 0:
                    di_gamma[t][i][j] = alpha[t][i] * self.transitions[i][j] * self.emissions[j][
                        observation] * beta[t + 1][j] / denom
                else:
                    di_gamma[t][i][j] = 0.

                gamma[t][i] += di_gamma[t][i][j]

    def __backward_pass(self, beta, observation, factors, t, A, B):
        """
        Compute beta values for time step t
        """
        N = self.transitions.shape[0]

        for i in range(N):
            sum = np.sum(A[i][:] * B[:][observation] * beta[t + 1][:])
            beta[t][i] = factors[t] * sum

    def __forward_pass(self, alpha, observations, factors, t, A, B):
        """
        Compute alpha values for time step t
        """
        N = self.transitions.shape[0]
        factors[t] = 0

        for i in range(N):
            alpha[t][i] = 0.00000

            for j in range(N):
                alpha[t][i] += alpha[t - 1][j] * A[j][i]

            alpha[t][i] *= B[i][observations[t]]
            factors[t] += alpha[t][i]

    @staticmethod
    def scale(matrix, factors, index):
        """
        Help function used for scaling the matrix to avoid underflow
        """
        factor = factors[index]

        if factor == 0:
            return

        factor = 1. / factor
        factors[index] = factor

        for i in range(matrix.shape[1]):
            matrix[index][i] *= factor


class Viterbi(object):
    def __init__(self):
        self.indices = []

    def run(self, transitions, emissions, distribution, observations):

        delta_matrices = self.calculate_deltas(transitions, emissions, distribution, observations)
        self.backtrack(delta_matrices)

    def backtrack(self, delta_matrices):

        last_delta_matrix = delta_matrices[-1]

        self.indices.append(np.argmax(last_delta_matrix[:, 0]))

        for i in range(len(delta_matrices) - 1):
            max_index = self.indices[-1]
            delta_matrix = delta_matrices.pop()
            self.indices.append(int(delta_matrix[max_index][1]))

        self.indices.reverse()

    def calculate_deltas(self, transitions, emissions, distribution, observations):

        observation = emissions[:, observations[0]]

        delta_matrices = []
        delta_matrix = Viterbi.initialize_delta_matrix(distribution, observation)
        delta_matrices.append(delta_matrix)

        for o in range(1, len(observations)):
            previous_delta_matrix = delta_matrices[-1]
            delta_matrix = np.zeros((transitions.shape[0], 2))
            observation = emissions[:, observations[o]]

            for i in range(transitions.shape[0]):
                delta_matrix[i][0] = -1
                delta_matrix[i][1] = 0

                for j in range(transitions.shape[1]):

                    dt = previous_delta_matrix[j][0] * transitions[j][i] * observation[i]

                    if dt > delta_matrix[i][0]:
                        delta_matrix[i][0] = dt
                        delta_matrix[i][1] = j

            delta_matrices.append(delta_matrix)

        return delta_matrices

    @staticmethod
    def initialize_delta_matrix(distribution, observations):

        multiply = np.multiply(distribution, observations)
        matrix = np.zeros((multiply.shape[0], 2))

        for i in range(matrix.shape[0]):
            matrix[i][0] = multiply[i]

        return matrix

    # def reestimate_transitions(self, observations, gamma, di_gamma, i):
    #     """
    #     Re-estimate transition matirx using gamma
    #     and di gamma values and scaling matrix after
    #     computations.
    #     :param observations: numpy array of observations
    #     :param gamma: numpy array of gamma values
    #     :param di_gamma: numpy array of di gamma values
    #     :param i: current iteration
    #     """
    #     N = self.transitions.shape[0]
    #     T = observations.shape[0]
    #     A = np.zeros(self.transitions.shape)
    #
    #     for j in range(N):
    #         self.transitions[i][j] = 0.
    #
    #         numer = 0.000000
    #         denom = 0.000000
    #
    #         for t in range(T - 1):
    #             numer += di_gamma[t][i][j]
    #             denom += gamma[t][i]
    #
    #         self.transitions[i][j] = 0.
    #
    #         if denom != 0.:
    #             self.transitions[i][j] = numer / denom
    #
    #         if self.transitions[i][j] == 0.:
    #             self.transitions[i][j] = 1e-16
    #
    #         self.transitions /= self.transitions.sum(axis=1)[:, np.newaxis]
    #     return A
    #
    # def reestimate_emissions(self, observations, gamma, i):
    #     """
    #     Re-estimate emission matrix using gamma values
    #     and scaling matrix after computations.
    #     :param observations: numpy array of observations
    #     :param gamma: numpy array of gamma values
    #     :param i: current iteration
    #     """
    #     N = self.emissions.shape[1]
    #     T = observations.shape[0]
    #
    #     for j in range(N):
    #         numer = 0.000000
    #         denom = 0.000000
    #
    #         for t in range(T - 1):
    #             if observations[t] == j:
    #                 numer += gamma[t][i]
    #             denom += gamma[t][i]
    #
    #         self.emissions[i][j] = 0.
    #
    #         if denom != 0.:
    #             self.emissions[i][j] = numer / denom
    #
    #         if self.emissions[i][j] == 0.:
    #             self.emissions[i][j] = 1e-16
    #
    #     self.emissions /= self.emissions.sum(axis=1)[:, np.newaxis]

    # def forward_pass(self, observations, factors):
    #     """
    #     Forward pass algorithm
    #     :param observations: numpy array of observations
    #     :param factors: factors used for scaling the numbers
    #     :return: matrix with alpha values
    #     """
    #
    #     N = self.transitions.shape[0]
    #     T = observations.shape[0]
    #
    #     alpha = np.zeros((T, N))
    #
    #     for i in range(N):
    #         alpha[0][i] = self.distribution[i] * self.emissions[i][observations[0]]
    #         factors[0] += alpha[0][i]
    #
    #     self.scale(alpha, factors, 0)
    #
    #     for t in range(1, observations.shape[0]):
    #         self.__forward_pass(alpha, observations, factors, t)
    #         self.scale(alpha, factors, t)
    #
    #     return alpha, factors

    # def __forward_pass(self, alpha, observations, factors, t):
    #     """
    #     Compute alpha values for time step t
    #     """
    #     N = self.transitions.shape[0]
    #     factors[t] = 0
    #
    #     for i in range(N):
    #         alpha[t][i] = 0.00000
    #
    #         for j in range(N):
    #             alpha[t][i] += alpha[t - 1][j] * self.transitions[j][i]
    #
    #         alpha[t][i] *= self.emissions[i][observations[t]]
    #         factors[t] += alpha[t][i]

    # def __backward_pass(self, beta, observation, factors, t):
    #     """
    #     Compute beta values for time step t
    #     """
    #     N = self.transitions.shape[0]
    #
    #     for i in range(N):
    #         sum = np.sum(self.transitions[i][:] * self.emissions[:][observation] * beta[t + 1][:])
    #         beta[t][i] = factors[t] * sum
