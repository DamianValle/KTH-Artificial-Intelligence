#!/usr/bin/env python3
# rewards: [golden_fish, jellyfish_1, jellyfish_2, ... , step]
rewards = [100, -10, -10, -10, -10, -10, -10, -10, -10, -10, -10, -10, -5]

# Q learning learning rate
alpha = 0.75

# Q learning discount rate
gamma = 0.5

# Epsilon initial
epsilon_initial = 1

# Epsilon final
epsilon_final = 0.25

# Annealing timesteps
annealing_timesteps = 1000

# threshold
threshold = 1e-6