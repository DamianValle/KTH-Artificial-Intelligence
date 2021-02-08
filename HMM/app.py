import json
import sys
from datetime import datetime
from io import UnsupportedOperation
from os.path import join
from pathlib import Path
from time import time
import os

import numpy as np
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder

from communicator import Communicator
from player_utils import Player
from sequences import Sequences
from shared import SettingLoader
from widgets import FishingDerby, TimeBoard, Fish, Stats

import constants

home = str(Path.home())


class Fishes(SettingLoader):
    def __init__(self):
        super().__init__()
        self.seq_types_fishes = None
        self.is_revealed = None
        self.observations_sequence = None  # Dictionary with the movements of each fish
        self.main_widget = None
        self.fishes = {}

    def init_fishes(self):
        """
        Initialize fishes and their parameters
        """
        space_subdivisions = 20
        range_x = [0.0 + x * 1.0 / space_subdivisions for x in range(space_subdivisions + 1)]
        range_y = [0.0 + x * 1.0 / space_subdivisions for x in range(space_subdivisions + 1)]

        n_types = 7

        self.seq_types_fishes = self.observations_sequence["fish_types"]
        self.is_revealed = [False] * len(self.seq_types_fishes)

        for fish_id, fish_type in enumerate(self.seq_types_fishes):
            init_x, init_y = self.observations_sequence["init_pos"][fish_id]
            random_x, random_y = 0, 0
            while range_x[random_x] < init_x:
                random_x += 1
            while range_y[random_y] < init_y:
                random_y += 1
            obs_seq = self.observations_sequence["sequences"][fish_id]

            name = f"fish{fish_id}"
            fish = Fish(init_state=(random_x, random_y),
                        type_fish=fish_type,
                        name=name,
                        observations_sequence=obs_seq,
                        settings=self.settings)
            self.main_widget.ids.fish_layout.add_widget(fish)
            self.fishes[name] = fish


class PrintScore1Player:
    def __init__(self):
        self.time = 0
        self.total_time = 0
        self.main_widget = None
        self.players = {}

    def print_score(self):
        print("Elapsed time:", str(self.time) + '/' + str(self.total_time), "s\tScore:", self.players[0].score)


class FishingDerbyApp(App, SettingLoader, Communicator):
    def __init__(self):
        App.__init__(self)
        SettingLoader.__init__(self)
        Communicator.__init__(self, receiver_threshold=constants.STEP_TIME_THRESHOLD)

        # Create class variables and set default values
        self.fishes = {}  # Dictionary of fishes
        self._cnt_steps = 0  # Count of the number of steps taken so far
        self.move_x = []  # Next moves of the fishes in the x axis
        self.move_y = []  # Next moves of the fishes in the y axis
        self.time = 0  # Seconds since start
        self.total_time = 60  # Total time of the game
        self.players = []  # Players list
        self.main_widget = None  # Main widget of the game
        self.time_board = None  # Time board widget
        # PID of the player loop in order to be able to kill it when the game is over
        self.player_loop = None
        self.observations_sequence = None
        self.models = None
        self.update_scheduled = None
        self.timer_scheduled = None

        self.frames_per_action = 10

    def on_stop(self):
        os.kill(self.player_loop.pid, 9)

    # Steps counter is a number that goes from 0 to 10
    @property
    def cnt_steps(self):
        return self._cnt_steps % self.frames_per_action

    @cnt_steps.setter
    def cnt_steps(self, val):
        self._cnt_steps = val

    def set_player_loop(self, player_loop):
        self.player_loop = player_loop

    def create_players(self):
        """Always 2 players, not necessarily 2 boats"""
        self.players = [Player(), Player()]

    def build(self):
        """Initialize the screen"""
        # Set sky color
        Window.clearcolor = 63 / 255, 191 / 255, 191 / 255, 0.3

        # Create main widget
        self.create_players()
        self.main_widget = FishingDerby(fishes=self.fishes,
                                        players=self.players,
                                        settings=self.settings)

        self.init_clock()

        self.init_specific()

        # Run initial update
        self.fishes_next_move()

        self.update_scheduled = Clock.schedule_interval(self.update, 1. / self.settings.frames_per_second)

        # GUI receives main widget and draws it
        return self.main_widget

    def update(self, dt):
        raise NotImplementedError

    def init_clock(self):
        """
        Initialize the timer
        :return:
        """
        n_seq = self.observations_sequence["n_seq"]
        self.total_time = n_seq * 10 * 1.0 / self.settings.frames_per_second
        self.time_board = TimeBoard(seconds=int(self.total_time))

        self.time_board.pos_hint['center_x'] = 0.5
        self.main_widget.add_widget(self.time_board)

        self.timer_scheduled = Clock.schedule_interval(self.update_clock, 1.0)

    def check_fish_near(self, boat):
        """
        Catch a random fish that is on the same position as the boat if possible
        :param boat: Boat. It must not have a caught fish.
        :return:
        """
        indices = np.random.permutation(len(self.fishes))
        keys = list(self.fishes.keys())
        for f in indices:
            fish = self.fishes[keys[f]]
            if fish.position == boat.hook.position and fish.caught is None:
                return fish

    def send_state_or_display_stats(self):
        """
        Send msg in order to indicate the player we have updated the game. If game has ended, display the stats screen.
        """
        msg = {
            "game_over": self.main_widget.game_over
        }
        if self.main_widget.game_over:
            self.timer_scheduled.cancel()
            self.update_scheduled.cancel()
            self.display_stats()
            self.sender(msg)
            os.kill(self.player_loop.pid, 9)
            return False

        self.update_specific(msg)

        return True

    def update_clock(self, dl):
        """
        Increase the clock by 1 second. If the remaining time is 0, the game is over.
        :param dl: delta-time. Not used.
        :return:
        """
        if self.time_board.seconds == 0:
            self.main_widget.game_over = True
        else:
            self.time_board.seconds -= 1
            self.time += 1.0

    def fishes_next_move(self):
        """
        Calculate and store, for every fish, the infinitesimal moving step for the position changing process.
        After that, increase each fish's updates counter.
        :return:
        """
        self.move_x.clear()
        self.move_y.clear()
        for fish in self.fishes.values():
            move_x, move_y = fish.next_movement_and_flip_horizontally()
            self.move_x += [move_x / self.frames_per_action]
            self.move_y += [move_y / self.frames_per_action]
            fish.updates_cnt += 1

    def check_fishes_caught(self):
        """
        For every boat in the game, do one of:
        1) if no fish is caught by it, check whether any can be caught
        2) if a fish has been caught and the player is at the surface, finish pulling the rod
        :return:
        """
        for player_number, player in enumerate(self.players):
            boat = player.boat
            if boat is None:
                continue
            elif boat.has_fish is None:
                fish_near = self.check_fish_near(boat)
                if fish_near is not None:
                    self.main_widget.ids.fish_layout.remove_widget(fish_near)
                    self.main_widget.ids.fish_layout.add_widget(fish_near)
                    boat.has_fish = fish_near
                    fish_near.caught = boat

            elif boat.has_fish is not None and boat.hook.position.y == 19:
                self.main_widget.finish_pulling_fish(player_number)

    def load_observations(self):
        """
        Load the observations file stated in the settings
        :return:
        """
        try:
            sequences = Sequences()
            sequences.load(sys.stdin)
            self.observations_sequence = sequences.data
        except AttributeError:
            print("Observations file not provided", file=sys.stderr)

    def init_specific(self):
        """
        Specific initialization of App. Abstract.
        :return:
        """
        raise NotImplementedError

    def update_specific(self, msg):
        """
        Specific action to perform in the loop with the message from the player controlled.
        :param msg:
        :return:
        """
        raise NotImplementedError

    def update_fishes_position_and_increase_steps(self):
        """
        Change the position of every fish by the amount inside move_x and move_y lists.
        After that, increase the updates counter of the game.
        :return:
        """
        for i, fish in enumerate(self.fishes.values()):
            fish.increase_x_y(self.move_x[i], self.move_y[i])
        self.cnt_steps += 1

    def calculate_strategy_for_next_frame_action(self):
        pass

    def display_stats(self):
        scores_file = join(home, ".fishing_derby_scores")
        stats = Stats(self.players, self.settings, self.fishes)
        with open(scores_file, "a") as f:
            try:
                stats_file = json.load(f)
            except UnsupportedOperation:
                stats_file = dict()

            stats_dict = stats.get_stats()

            stats_file[datetime.now().timestamp()] = stats_dict
            json.dump(stats_file, f)

            stats.load(stats_dict)
        stats.open()


class FishingDerbyHMMApp(FishingDerbyApp, Fishes, PrintScore1Player):
    def __init__(self):
        super().__init__()
        Builder.load_file('main.kv')
        self.p1_hmm_model = None  # Hidden markov model used by the second player
        self.correct_guesses = 0  # Number of correct guesses so far
        self.total_guesses = 0    # Number of total guesses so far
        self.num_fishes = 0
        self.initial_time = None
        self.final_time = None

    def update_clock(self, dl):
        super().update_clock(dl)
        self.print_score()

    def build(self):
        self.load_observations()
        widget = super().build()
        return widget

    def init_specific(self):
        self.init_fishes()
        self.num_fishes = len(self.fishes)

    def create_players(self):
        """Always 1 player"""
        self.players = [Player()]

    def calculate_strategy_for_next_frame_action(self):
        msg = self.receiver()
        self.final_time = time()
        if 'timeout' in msg and msg['timeout'] or self.final_time - self.initial_time >= self.settings.time_threshold:
            self.main_widget.game_over = True
            print('Timeout error!')
            self.correct_guesses = 0

        if self.total_guesses == self.num_fishes:
            self.main_widget.game_over = True

        if self.main_widget.game_over:
            os.kill(self.player_loop.pid, 9)
        else:
            msg_reveal = self.evaluate_guess(msg)
            if msg_reveal["reveal"]:
                self.sender(msg=msg_reveal)

        self.fishes_next_move()

    def evaluate_guess(self, msg):
        msg_reveal = {"game_over": False, "reveal": False}
        if 'guessing' in msg and msg["guessing"]:
            fish_id = msg["id"]
            guess = msg["type"]
            correct = guess == self.seq_types_fishes[fish_id]
            if not self.is_revealed[fish_id]:  # if the fish was not revealed before
                self.is_revealed[fish_id] = True
                self.total_guesses += 1
                if correct:
                    self.correct_guesses += 1
                    self.fishes["fish" + str(fish_id)].guessed = True
                    self.fishes["fish" + str(fish_id)].color = [1.0, 1.0, 1.0, 1.0]
                    self.players[0].score = self.correct_guesses
                    self.main_widget.update_score(int(self.correct_guesses), 0)
                else:
                    self.fishes["fish" + str(fish_id)].color = [1.0, 1.0, 1.0, 0.25]

            msg_reveal["reveal"] = True
            msg_reveal["correct"] = correct
            msg_reveal["game_over"] = self.total_guesses == self.num_fishes
            msg_reveal["id"] = fish_id
            msg_reveal["type"] = self.seq_types_fishes[fish_id]

        return msg_reveal

    def update_specific(self, msg):
        for k in self.fishes.keys():
            msg[k] = self.fishes[k].observation
        self.sender(msg)
        self.initial_time = time()

    def update(self, dt):
        # update game
        if self.cnt_steps == 0 and self._cnt_steps > 0:
            # Check if a fish is to be caught by any of the players
            self.check_fishes_caught()

            # Check if game is about to timeout
            if self.time >= self.total_time:
                self.main_widget.game_over = True

            if self.send_state_or_display_stats() is False:
                return

            self.calculate_strategy_for_next_frame_action()

        self.update_fishes_position_and_increase_steps()
