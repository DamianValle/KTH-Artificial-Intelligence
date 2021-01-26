# Game tree for Fishing Derby
from itertools import product
import numpy as np
from fishing_game_core.shared import OBS_TO_MOVES, ACT_TO_MOVES
from copy import deepcopy


class State:
    def __init__(self, number_of_fish):
        # The current player's index - 0 means MAX and 1 means MIN.
        self.player = None
        # The player scores: {0: MAX_SCORE, 1: MIN_SCORE}
        self.player_scores = {}
        # The index of the caught fish for the two players in a dict.
        # The fish index -1 means that no fish has been caught.
        self.player_caught = {}
        # The positions of the two hooks, provided as (x,y) coordinate tuples.
        self.hook_positions = {}
        # The positions of the uncaught fishes, provided as (x,y) coordinate tuples.
        self.fish_positions = {}
        # The score values associated with each fish index.
        self.fish_scores = {}

    def set_hook_positions(self, player_pos):
        """
        Set the hooks positions for each player
        :param hook_pos
        :return:
        """
        p0 = player_pos[0], player_pos[1]
        p1 = player_pos[2], player_pos[3]
        self.hook_positions = {0: p0, 1: p1}

    def set_player(self, player):
        """
        Set current player.
        :param player: either 0 or 1
        :return:
        """
        self.player = player

    def set_player_scores(self, score_p0, score_p1):
        """
        Set current games scores for each player
        :param scores:
        :return:
        """
        self.player_scores = {0: score_p0, 1: score_p1}

    def set_fish_scores(self, fish_scores):
        """
        Set scores of fish
        :param fish_scores:
        :return:
        """
        self.fish_scores = deepcopy(fish_scores)

    def set_caught(self, caught):
        """
        Set currently caught fish for every player
        :param caught: tuple of either the fish_numbers or None when no fish has been caught
        :return:
        """
        p0_caught = caught[0] if caught[0] is not None else -1
        p1_caught = caught[1] if caught[1] is not None else -1
        self.player_caught = {0: p0_caught, 1:p1_caught}

    def set_fish_positions(self, fish_number, pos):
        """
        Set the position of the fish.
        :param fish_number: integer
        :param pos: tuple positions in x and y
        :return:
        """
        self.fish_positions[fish_number] = pos

    def get_hook_positions(self):
        """
        Return the hooks positions
        :return: dict of 2-tuples with (x, y) values of each player's hook
        """
        return self.hook_positions

    def get_player(self):
        """
        Return the current player's index
        :return: either 0 or 1
        """
        return self.player

    def get_player_scores(self):
        """
        Returns the score for each player
        :return:
        """
        return self.player_scores[0], self.player_scores[1]

    def get_fish_scores(self):
        """
        Return scores of fish
        :return:
        """
        return self.fish_scores

    def get_caught(self):
        """
        Return the caught fish of each player
        :return: 2-tuple with the corresponding fish_number or None for each player
        """
        p0 = self.player_caught[0]
        if p0 == -1:
            p0 = None
        p1 = self.player_caught[1]
        if p1 == -1:
            p1 = None
        return p0, p1

    def get_fish_positions(self):
        """
        Return dict of fish positions in current state
        :return: dict of fish_numbers -> 2-tuple with position (x, y)
        """
        return self.fish_positions

    def __repr__(self):
        """
        Return array visualization of the state. Meant for visualization on a debugger.
        :return: str
        """
        return f"{self.data.tolist()}"

    def remove_fish(self, fish_number):
        """
        Remove fish from state (because it is pulled in)
        :param fish_number:
        :return:
        """
        del self.fish_positions[fish_number]


def compute_caught_fish(state, current_fishes_on_rod):
    """
    Infer caught fish tuple from the state
    :param state: a state instance
    :return: 2-tuple - caught fish for each player
    """
    caught_fish = [None, None]
    pull_in_fishes = [None, None]
    hook_positions = state.get_hook_positions()
    fish_positions = state.get_fish_positions()
    for player_number in hook_positions:
        if current_fishes_on_rod[player_number] is not None:
            # A fish was already attached in the previous step
            fish_number = current_fishes_on_rod[player_number]
            if fish_positions[fish_number][1] >= 19:
                pull_in_fishes[player_number] = fish_number
            else:
                caught_fish[player_number] = fish_number
        else:
            # Player did not have a fish attached to rod
            for fish_number in fish_positions:
                if hook_positions[player_number] == fish_positions[fish_number]:
                    # Pull fish in if it is on the surface
                    if fish_positions[fish_number][1] >= 19:
                        pull_in_fishes[player_number] = fish_number
                    else:
                        caught_fish[player_number] = fish_number
                    break
    return caught_fish, pull_in_fishes


class Node:
    def __init__(self, root=True, message=None, player=0):
        # A list of the child Nodes, found one level below in the game tree. 
        # NOTE: this field has to be initialized by self.compute_and_get_children().
        self.children = []
        # The current state of the game. See the State class for more information.
        self.state = None
        # The parent Node in the game tree.
        self.parent = None
        # The action that led to this node in the game tree, represented as an int.
        # Can be transformed to a string (e.g. "left") using ACTION_TO_STR in shared.py.
        self.move = None
        # This field can be ignored for this assignment.
        self.probability = 1.0

        if root:
            # Initialize the following fields:
            #   self.depth (the depth level at the current node - 0 at the root)
            #   self.player (the current player's index; MAX is 0 and MIN is 1)
            self.initialize_root(message, player)

    def add_child(self, state: State, move: int, depth: int = 0, observations: dict = {}, probability: float = 1.0):
        """
        Add a new node as a child of current node
        :param state: child's state
        :param move: child's move
        :param probability: probability of accessing child
        :param depth: depth of the child
        :observations: observations of the game
        :return:
        """
        new_node = self.__class__(root=False)
        new_node.state = state
        new_node.parent = self
        new_node.move = move
        new_node.depth = depth
        new_node.observations = observations
        self.children.append(new_node)

        new_node.probability = probability
        return new_node

    def initialize_root(self, curr_state, player):
        """
        Initialize root node.
        :param curr_state: parsed dict coming from game_controller
        :return:
        """

        self.depth = 0
        self.player = player # Root's player
        obs = curr_state["observations"]
        keys = sorted(obs.keys())
        obs = np.array([np.array(obs[k]) for k in keys])
        obs = obs.T
        obs = {i: j.tolist() for i, j in enumerate(obs)}
        self.observations = obs
        # Translate message state into state object
        curr_state_s = State(len(curr_state["fishes_positions"].keys()))
        curr_state_s.set_player(self.player)
        curr_state_s.set_hook_positions(
            (*curr_state["hooks_positions"][0], *curr_state["hooks_positions"][1]))
        curr_state_s.set_caught(
            (curr_state["caught_fish"][0], curr_state["caught_fish"][1]))
        for i, f in curr_state["fishes_positions"].items():
            curr_state_s.set_fish_positions(i, f)

        # Set score of players
        player_scores = curr_state["player_scores"]
        curr_state_s.set_player_scores(player_scores[0], player_scores[1])

        # Set score, i.e. points, for fishes
        fish_scores = curr_state["fish_scores"]
        curr_state_s.set_fish_scores(fish_scores)

        self.state = curr_state_s  # Root's state object

    def compute_and_get_children(self):
        """
        Populate the node with its children. Then return them.
        :param:
        :return: list of children nodes
        """

        if len(self.observations) == self.depth: # Cannot compute children any longer
            return []
        
        if len(self.children) != 0: # If we already compute the children 
            return self.children 

        current_player = self.state.get_player()
        caught = self.state.get_caught()
        if caught[current_player] is not None:
            # Next action is always up for the current player
            new_state = self.compute_next_state(self.state, 1, self.observations[self.depth])
            self.add_child(new_state, 1, self.depth+1, self.observations)
        else:
            # Any action is possible
            for act in range(5):
                new_state = self.compute_next_state(
                    self.state, act, self.observations[self.depth])
                self.add_child(new_state, act, self.depth+1, self.observations)

        return self.children

    def compute_next_state(self, current_state, act, observations):
        """
        Given a state and an action, compute the next state. Add the next observations as well.
        :param current_state: current state object instance
        :param act: integer of the move
        :param observations: list of observations for current fish
        :return:
        """
        current_player = current_state.get_player()
        next_player = 1 - current_player
        fish_states = current_state.get_fish_positions()
        hook_states = current_state.get_hook_positions()
        new_state = State(len(fish_states.keys()))
        new_state.set_player(next_player)
        current_fishes_on_rod = current_state.get_caught()
        self.compute_new_fish_states(new_state, fish_states, observations, current_player, fishes_on_rod=current_fishes_on_rod)
        new_hook_positions = self.compute_new_hook_states(
            hook_states, current_player, ACT_TO_MOVES[act])
        new_state.set_hook_positions(new_hook_positions)

        # Get player scores for new state
        score_p0, score_p1 = current_state.get_player_scores()

        # Set fish scores for new state
        new_state.set_fish_scores(current_state.get_fish_scores())

        # Compute the fish that are currently caught by players
        next_caught_fish, pull_in_fishes = compute_caught_fish(new_state, current_fishes_on_rod)

        # Update player scores and remove fishes that are caught and at the surface
        fish_score_points = new_state.get_fish_scores()
        for i_player, fish_number in enumerate(pull_in_fishes):
            if fish_number is not None:
                if i_player == 0:
                    score_p0 += fish_score_points[fish_number]
                else:
                    score_p1 += fish_score_points[fish_number]

                # Remove fish
                new_state.remove_fish(fish_number)

        # Update players scores
        new_state.set_player_scores(score_p0, score_p1)

        new_state.set_caught(next_caught_fish)

        return new_state

    def compute_new_hook_states(self, current_hook_states, current_player, move):
        """
        Compute the hook states after a certain move
        :param current_hook_states: 4-iterable with (x, y) positions of player 0's hook and (x, y) of player 1's hook
        :param current_player: either 0 or 1
        :param move: integer. current_player's action
        :return: 4 elements list with new (x, y) positions of player 0's hook and (x, y) of player 1's hook
        """
        new_hook_states = [0, 0, 0, 0]
        next_player = 1 - current_player

        hook_position_next_player = current_hook_states[next_player]
        new_hook_states[next_player * 2] = hook_position_next_player[0]
        new_hook_states[next_player * 2 + 1] = hook_position_next_player[1]

        hook_position_current_player = self.xy_move(
            current_hook_states[current_player], move, current_hook_states[next_player])
        new_hook_states[current_player * 2] = hook_position_current_player[0]
        new_hook_states[current_player * 2 +
                        1] = hook_position_current_player[1]

        return new_hook_states

    def compute_new_fish_states(self, new_state, current_fish_positions, observations, current_player, fishes_on_rod=None):
        """
        Compute the new fish states given the observations
        :param new_state: state instance where to save the new fish positions
        :param current_fish_positions: map: fish_number -> (x, y) position of the fish
        :param observations: list of observations, in the order of the sorted keys of the remaining fishes
        :return:
        """
        for i, k in enumerate(sorted(current_fish_positions.keys())):

            if fishes_on_rod[current_player] == k:
                # Fishes on rod of current player can only move up
                new_fish_obs_code = OBS_TO_MOVES[0]
            elif fishes_on_rod[1-current_player] == k:
                # Fishes on rod of other player do not move
                new_fish_obs_code = (0,0)
            else:
                obs = observations[i]
                new_fish_obs_code = OBS_TO_MOVES[obs]

            curr_pos = current_fish_positions[k]
            new_state.set_fish_positions(k, self.xy_move(curr_pos, new_fish_obs_code))

    def xy_move(self, pos, move, adv_pos = None):
        """
        Return the (x, y) position after a given move of the tuple pos. Wraps the x axis so that trespassing the right
        margin means appearing in the left and vice versa. Makes sure the hooks cannot cross each other.
        :param pos: 2-tuple. Current position (x, y)
        :param move: 2-tuple. Desired move.
        :return: 2-tuple. pos + move corrected to be in the margins [0, space_subdivisions)
        """
        space_subdivisions = 20
        pos_x = (pos[0] + move[0] + space_subdivisions) % space_subdivisions
        pos_y = pos[1] + move[1]
        if not 0 <= pos_y < space_subdivisions:
            pos_y = pos[1]
        if adv_pos is not None:
            if pos_x == adv_pos[0]:
                return pos[0], pos_y

        return pos_x, pos_y
