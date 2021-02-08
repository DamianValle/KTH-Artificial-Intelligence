#!/usr/bin/env python3
import random
import math

from fishing_game_core.game_tree import Node
from fishing_game_core.player_utils import PlayerController
from fishing_game_core.shared import ACTION_TO_STR

import time


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


class PlayerControllerMinimax(PlayerController):

    def __init__(self):
        super(PlayerControllerMinimax, self).__init__()

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
        return None

    def calculate_heuristics(self, node):
        """
        Computes a heuristic for a particular node.
        :param node: Given node
        :type node: game_tree.Node
        :return: Heuristic score
        :rtype: float
        """

        total_score = node.state.player_scores[0] - node.state.player_scores[1]

        h = 0
        for i in node.state.fish_positions:
            distance = self.l1_distance(node.state.fish_positions[i], node.state.hook_positions[0])
            if distance == 0 and node.state.fish_scores[i] > 0:
                return float('inf')
            h = max(h, node.state.fish_scores[i] * math.exp(-distance))

        return 2 * total_score + h

    def l1_distance(self, fish_positions, hook_positions):
        """
        Computes the Manhattan distance between the player hook and a given fish
        :param hook_positions: Position of the player's hook
        :type hook_positions: array
        :param fish_positions: Position of a given fish
        :type fish_positions: array
        :return: Manhattan distance
        :rtype: int
        """

        y = abs(fish_positions[1] - hook_positions[1])

        delta_x = abs(fish_positions[0] - hook_positions[0])
        x = min(delta_x, 20 - delta_x)

        return x + y

    def alphabeta(self, node, state, depth, alpha, beta, player, initial_time,seen_nodes):
        """
        Performs the alpha beta pruning search algorithm
        """

        if time.time() - initial_time > 0.055:
            raise TimeoutError
        else:
            k = self.hash_key(state)
            if k in seen_nodes and seen_nodes[k][0] >= depth:
                return seen_nodes[k][1]
            children = node.compute_and_get_children()
            children.sort(key=self.calculate_heuristics, reverse = True)
            if depth == 0 or len(children) == 0:
                v = self.calculate_heuristics(node)
            elif player == 0:
                v = float('-inf')
                for child in children:
                    v = max(v, self.alphabeta(child, child.state, depth - 1, alpha, beta, 1, initial_time,seen_nodes))
                    alpha = max(alpha, v)
                    if alpha >= beta:
                        break
            else:
                v = float('inf')
                for child in children:
                    v = min(v, self.alphabeta(child, child.state, depth - 1, alpha, beta, 0, initial_time,seen_nodes))
                    beta = min(beta, v)
                    if beta <= alpha:
                        break

            key = self.hash_key(state)
            seen_nodes.update({key:[depth,v]})
        return v

    def hash_key(self, state):
        """
        Computes the string hash of a given state using the hook positions and fish positions+scores
        :param state: Node state
        :type state: game_tree.State
        :return: Hashed state
        :rtype: str
        """

        # Zugzwang?

        pos_dic = dict()
        for pos, score in zip(state.get_fish_positions().items(), state.get_fish_scores().items()):
            score = score[1]
            pos = pos[1]
            x = pos[0]
            y = pos[1]
            k = str(x) + str(y)
            pos_dic.update({k:score})

        return str(state.get_hook_positions())+str(pos_dic)

    def depth_search(self, node, depth, initial_time, seen_nodes):
        """
        Performs an alpha-beta pruning search for depth layers
        :param node: Root node
        :type node: game_tree.Node
        :param depth: Number of layers deep to search
        :type depth: int
        :param initial_time: initial_time time of the search
        :type initial_time: datetime.time
        :param seen_nodes: Already visited nodes
        :type seen_nodes: dict
        :return: Encoded move that leads to the best scoring node
        :rtype: int
        """

        alpha = float('-inf')
        beta = float('inf')

        children = node.compute_and_get_children()

        scores = []
        for child in children:
            score = self.alphabeta(child, child.state, depth, alpha, beta, 1, initial_time, seen_nodes)
            scores.append(score)

        best_score_idx = scores.index(max(scores))

        return children[best_score_idx].move

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

        initial_time = time.time()
        depth = 0
        timeout = False
        seen_nodes = dict()
        best_move = 0

        while not timeout:
            try:
                move = self.depth_search(initial_tree_node, depth, initial_time, seen_nodes)
                depth += 1
                best_move = move
            except:
                timeout = True

        return ACTION_TO_STR[best_move]