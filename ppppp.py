import math
import re
from time import time

from fishing_game_core.game_tree import Node
from fishing_game_core.player_utils import PlayerController
from fishing_game_core.shared import ACTION_TO_STR

DEPTH = 9
TIME_OUT = 60 * 1e-3


class PlayerControllerHuman(PlayerController):
    def player_loop(self):
        """
        Function that generates the loop of the game. In each iteration
        the human plays through the keyboard and send
        this to the game through the sender. Then it receives an
        update of the game through receiver, with this it computes the
        next movement.
        :return:
        """

        while True:
            # send message to game that you are ready
            msg = self.receiver()
            if msg["game_over"]:
                return


def sort_nodes(state):
    node = state.state
    scores = node.player_scores
    return (scores[0] - scores[1]) - len(node.fish_positions)


def alphabeta(state, depth, alpha, beta, player, model):
    hash_state = hash_states(state)
    if hash_state in model.seen_states:
        return model.seen_states[hash_state]

    time_t = time() - model.time_start
    if time_t >= TIME_OUT:
        raise TimeoutError

    children = sorted(state.compute_and_get_children(), key=heuristic, reverse=True)
    # children = sorted(state.compute_and_get_children(), key=sort_nodes, reverse=True)
    # children = state.compute_and_get_children()

    if depth == 0 or not children:  # or terminal_state(state):
        v = heuristic(state)

    elif player == 0:
        v = -math.inf
        for child in children:
            v = max(v, alphabeta(child, depth - 1, alpha, beta, 1, model))
            if v > alpha:
                alpha = v
                if depth == model.depth_temp:
                    model.node = child
            if beta <= alpha:
                break
    else:
        v = math.inf
        for child in children:
            v = min(v, alphabeta(child, depth - 1, alpha, beta, 0, model))
            beta = min(beta, v)
            if beta <= alpha: break
    model.seen_states[hash_state] = v
    return v


class MinimaxModel:

    def __init__(self, initial_data, depth, node=None):
        self.initial_data = initial_data
        self.depth = depth
        self.depth_temp = depth
        self.node = node
        self.time_start = time()
        self.seen_states = {}
        self.time_out = 0
        self.last = 0
        self.hash_count = 0


def hash_states(state):
    node = state.state
    sr = str(node.get_hook_positions()) + str(node.get_fish_positions()) + str(node.player)  # + str(node.player_scores)
    # sr +=
    return sr


def distance(fish, us, their):
    """
    distance is measured in how many moves we need to reach the fish at that point
    """

    x = abs(us[0] - fish[0])
    y = abs(us[1] - fish[1])

    if fish[0] >= their[0]:
        x = 20 - x 

    return x + y


def heuristic(state):
    node = state.state
    scores = node.player_scores
    fish_positions = node.fish_positions
    len_fish_positions = len(fish_positions)

    if len_fish_positions == 0:
        return 100 * (scores[0] - scores[1])

    our_position, their_position = node.get_hook_positions().values()
    v = 0
    for fish, position in fish_positions.items():
        dist = distance(position, our_position, their_position)
        if dist == 0 and len_fish_positions == 1: return math.inf
        v += 5 * node.fish_scores[fish] / dist if dist != 0 else 5 * node.fish_scores[fish]

    v = 10 * (scores[0] - scores[1]) + (v / len_fish_positions) - len_fish_positions
    return v


class PlayerControllerMinimax(PlayerController):

    def __init__(self):
        super(PlayerControllerMinimax, self).__init__()
        self.count = 0

    def player_loop(self):
        """
        Main loop for the minimax next move search.
        :return:
        """

        # Generate game tree object
        first_msg = self.receiver()
        # Initialize your minimax model
        model = self.initialize_model(initial_data=first_msg)

        while True:
            msg = self.receiver()

            # Create the root node of the game tree
            node = Node(message=msg, player=0)

            # Possible next moves: "stay", "left", "right", "up", "down"
            best_move = self.search_best_next_move(
                model=model, initial_tree_node=node)

            # Execute next action
            self.sender({"action": best_move, "search_time": None})

    def initialize_model(self, initial_data):
        """
        Initialize your minimax model
        :param initial_data: Game data for initializing minimax model
        :type initial_data: dict
        :return: Minimax model
        :rtype: object
        Sample initial data:
        { 'fish0': {'score': 11, 'type': 3},
          'fish1': {'score': 2, 'type': 1},
          ...
          'fish5': {'score': -10, 'type': 4},
          'game_over': False }
        Please note that the number of fishes and their types is not fixed between test cases.
        """
        # EDIT THIS METHOD TO RETURN A MINIMAX MODEL ###
        return MinimaxModel(initial_data, DEPTH)

    def search_best_next_move(self, model, initial_tree_node):
        """
        Use your minimax model to find best possible next move for player 0 (green boat)
        :param model: Minimax model
        :type model: object
        :param initial_tree_node: Initial game tree node
        :type initial_tree_node: game_tree.Node
            (see the Node class in game_tree.py for more information!)
        :return: either "stay", "left", "right", "up" or "down"
        :rtype: str
        """

        # EDIT THIS METHOD TO RETURN BEST NEXT POSSIBLE MODE FROM MINIMAX MODEL ###

        # NOTE: Don't forget to initialize the children of the current node
        #       with its compute_and_get_children() method!

        model.time_start = time()

        if initial_tree_node.state.player_caught[0] != -1:
            return ACTION_TO_STR[1]

        for i in range(1, model.depth + 1):
            try:
                model.depth_temp = i
                model.seen_states = {}
                v = alphabeta(initial_tree_node, i, -math.inf, math.inf, initial_tree_node.player, model)
                move = model.node.move
                if v == math.inf:
                    break
            except TimeoutError:
                model.time_out += 1
                break

        return ACTION_TO_STR[move]