#!/usr/bin/env python3
import random
import time
import math

from fishing_game_core.game_tree import Node
from fishing_game_core.player_utils import PlayerController
from fishing_game_core.shared import ACTION_TO_STR


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

        return None

    def l1_distance(self, fish_position, hook_positions):
        """
        Computes the distance from the hook to the fish position 
        taking into account the opponent in the middle
        """

        player_hook = hook_positions[0]
        opponent_hook = hook_positions[1]

        x = abs(player_hook[0] - fish_position[0])
        y = abs(player_hook[1] - fish_position[1])

        if player_hook[0] < opponent_hook[0] <= fish_position[0] or fish_position[0] <= opponent_hook[0] < player_hook[0]:
            x = 20 - x

        return x + y

    def heuristic(self, node):
        """
        Computes the heuristic of a given node
        """

        total_score = node.state.player_scores[0] - node.state.player_scores[1]

        len_fish = len(node.state.fish_positions)

        if len_fish==0:
            return 100*total_score

        h = 0
        for fish, position in node.state.fish_positions.items():
            distance = self.l1_distance(position, node.state.get_hook_positions())
            # len(node.state.fish_positions.items())==1???
            if(distance==0 and len_fish ==1 and node.state.fish_scores[fish] > 0): 
                return float('inf')
            h += 5 * node.state.fish_scores[fish] / (distance + (distance==0))

        return 10 * total_score + 5 * (h / len_fish) - len_fish

    def alphabeta(self, alpha, beta, node, depth, player, seen_nodes, initial_time):
        """
        Performs the alpha beta pruning search algorithm
        """

        self.check_timeout(initial_time)

        hash = self.hash_state(node.state)
        if(hash in seen_nodes):
            return seen_nodes[hash]

        children = sorted(node.compute_and_get_children(), key=self.heuristic, reverse=True)

        if(depth == 0 or not children):
            v = self.heuristic(node)
        elif player == 0:
            v = float('-inf')
            for child in children:
                v = max(v, self.alphabeta(alpha, beta, child, depth - 1, 1, seen_nodes, initial_time))
                alpha = max(alpha, v)
                if(alpha >= beta):
                    break
        else:
            v = float('inf')
            for child in children:
                v = min(v, self.alphabeta(alpha, beta, child, depth-1, 0, seen_nodes, initial_time))
                beta = min(beta, v)
                if(alpha >= beta):
                    break

        seen_nodes[hash] = v
        return v

    def hash_state(self, state):
        """
        Computes the hash of a state
        :param state: Node state
        :type state: game_tree.State
        :return: Hash of the state
        :rtype: str
        """
        #   Preguntandome si necesitamos el player o los hook positions del otro
        #   Probablemente si pero que mas da, mas rapido
        return str(state.player) + str(state.get_fish_positions()) + str(state.get_hook_positions())

    def check_timeout(self, initial_time):
        """
        Raises a TimeoutError exception if the search time has exceeded 50ms
        """

        if(time.time()-initial_time > 0.06):
            raise TimeoutError

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
            score = self.alphabeta(alpha, beta, child, depth, node.player, seen_nodes, initial_time)
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
        seen_nodes = dict() # Maybe put move this to depth search to make it clean.
        depth = 0
        timeout = False
        best_move = 0

        while not timeout:
            try:
                best_move = self.depth_search(initial_tree_node, depth, initial_time, seen_nodes)
                seen_nodes.clear()
                depth+=1
            except:
                timeout = True

        # 0: "stay", 1: "up", 2: "down", 3: "left", 4: "right"
        return ACTION_TO_STR[best_move]