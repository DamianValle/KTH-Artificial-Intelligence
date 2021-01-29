#!/usr/bin/env python3
import random
import time

from fishing_game_core.game_tree import Node
from fishing_game_core.player_utils import PlayerController
from fishing_game_core.shared import ACTION_TO_STR

def compute_heuristic(node):
    """
    Compute a heuristic score value for a given node.
    :param node: Tree node
    :type node: game_tree.Node
        (see the Node class in game_tree.py for more information!)
    :return: score value (should be positive if Node is good for MAX)
    :rtype: int
    """
    print("Player is: ")
    print(node.state.get_player())

    print("Hook positions: ")
    print(node.state.get_hook_positions())

    return None

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
        print("Initial_data length: " + str(len(initial_data)))
        print(initial_data['game_over'])
        for element in initial_data:
            print(element)


        return None

    

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

        random_move = random.randrange(5)

        t1 = time.time()

        

        initial_tree_node.compute_and_get_children()

        for child in initial_tree_node.children:
            compute_heuristic(child)

        #next_state = initial_tree_node.compute_next_state(initial_tree_node, 3, initial_tree_node.observations)

        #print(next_state)
        #print(children)

        # len(children) appears to be always 5.

        #How to implement timeout? Maybe signals?

        t2 = time.time()

        print("Total runtime: {:.2f}ms".format((t2-t1)*1000))



        # 0: "stay", 1: "up", 2: "down", 3: "left", 4: "right"
        return ACTION_TO_STR[random_move]

    