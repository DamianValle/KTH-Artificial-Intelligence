from time import time
import numpy as np
import random

from kivy.clock import Clock
from kivy.core.window import Window

import platform
import opponent

from fishing_game_core.app import FishingDerby, FishingDerbyApp, Fishes, PrintScore2Players, GamesWithBoats
from fishing_game_core.game_tree import Node


class FishingDerbyMinimaxApp(FishingDerbyApp, Fishes, PrintScore2Players, GamesWithBoats):
    def __init__(self):
        super().__init__()
        self.minimax_agent_opponent = None  # Implemented minimax model used by the second player
        self.space_subdivisions = None  #
        self.current_player = 0  # Player that starts moving
        self.time_sent = None  # Time of last sent state to player loop
        self.time_received = None  # Time of last receive state from player loop
        self.n_timeouts = 0
        self.load_observations()

    def update_clock(self, dl):
        super().update_clock(dl)
        self.print_score()

    def update(self, dt):
        # update game
        if self._cnt_steps % self.settings.frames_per_action == 0 and self._cnt_steps > 0:

            # Set position of caught fish to position of hook
            for k,fish in self.fishes.items():
                if fish.caught is not None:
                    fish.position.set_y(fish.caught.hook.position.y)

            # Check if a fish is to be caught by any of the players
            self.check_fishes_caught()

            # Check if there are fish left and if not, execute action
            if len(self.fishes) == 0:
                self.do_when_no_fish_left()

            # Check if game is about to timeout
            if self.time >= self.total_time:
                self.main_widget.game_over = True

            # Continue updating
            self.current_player = 1 - self.current_player

            # Send current state to player_controller class
            if self.send_state_or_display_stats() is False:
                return

            # Update decisions
            self.calculate_strategy_for_next_frame_action()

        self.update_fishes_position_and_increase_steps()

        self.execute_action()

    def build(self):
        """Initialize the Kivy screen"""
        # Set sky color
        Window.clearcolor = 63 / 255, 191 / 255, 191 / 255, 0.3

        # Create main widget
        self.load_observations()
        self.create_players()
        self.main_widget = FishingDerby(fishes=self.fishes,
                                        players=self.players,
                                        settings=self.settings)

        self.init_clock()

        self.init_specific()

        # Run initial update
        self.fishes_next_move()

        self.update_scheduled = Clock.schedule_interval(
            self.update, 1.0 / self.settings.frames_per_second)

        # Kivy receives main widget and draws it
        return self.main_widget

    def send_first_message(self):
        msg = {}
        for name, fish in self.fishes.items():
            msg[name] = {"type": fish.type_fish, "score": fish.score}
        msg["game_over"] = False
        self.sender(msg)

    def init_minimax(self):
        self.space_subdivisions = self.settings.space_subdivisions
        self.send_first_message()

        initial_data = {}
        for name, fish in self.fishes.items():
            initial_data[name] = {"type": fish.type_fish, "score": fish.score}
        initial_data["game_over"] = False

        # Initialize opponent
        self.minimax_agent_opponent = opponent.MinimaxModel(initial_data, self.space_subdivisions)

    def init_specific(self):
        self.init_fishes()
        self.init_minimax()
        self.introduce_boats_to_screen(2)

    def calculate_strategy_for_next_frame_action(self):
        # Receive action from player_controller
        if self.current_player == 0:
            msg = self.receiver()
            self.latest_msg = msg # Added this for printing search time.
            self.time_received = time()
            self.check_time_threshold()
            self.new_action(msg)

        # Calculate fishes next move
        self.fishes_next_move()

    def build_minimax_msg(self, msg):
        msg["hooks_positions"] = {}
        msg["fishes_positions"] = {}
        msg["observations"] = {}
        msg["fish_scores"] = {}

        for i, player in enumerate(self.players):
            boat = player.boat
            msg["hooks_positions"][i] = (
                boat.hook.position.x, boat.hook.position.y)

        for k, fish in self.fishes.items():
            n = int(k[4:])
            msg["fishes_positions"][n] = (fish.position.x, fish.position.y)
            st = fish.updates_cnt
            msg["observations"][n] = fish.observations_sequence[st:]
            msg["fish_scores"][n] = fish.score

        caught_fish_names = {0: None,
                             1: None}

        for p in range(len(self.players)):
            if self.players[p].boat.has_fish is not None:
                caught_fish_names[p] = int(
                    self.players[p].boat.has_fish.name[4:])

        msg["player_scores"] = {}
        msg["player_scores"][0] = self.players[0].score
        msg["player_scores"][1] = self.players[1].score

        msg["caught_fish"] = caught_fish_names
        return msg

    def update_specific(self, msg):
        msg = self.build_minimax_msg(msg)
        if self.current_player == 0:
            self.sender(msg)
            self.time_sent = time()
        else:
            initial_tree_node = Node(message=msg, player=1)
            self.action = self.minimax_agent_opponent.next_move(initial_tree_node)

    def do_when_no_fish_left(self):
        self.main_widget.game_over = True
        self.reinitialize_count()

    def execute_action(self):

        if self.players[self.current_player].boat.has_fish:
            self.action = "up"

        self.main_widget.act(self.action, player=self.current_player)

    def reinitialize_count(self):
        self._cnt_steps = 0

    def check_time_threshold(self):
        if self.time_received - self.time_sent > self.settings.time_threshold:
            self.n_timeouts += 1
            if self.n_timeouts >= 3:
                raise TimeoutError
        else:
            self.n_timeouts = 0

    @staticmethod
    def set_seed(seed):
        random.seed(seed)
        np.random.seed(seed)
