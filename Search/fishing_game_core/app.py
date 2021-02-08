import sys
import json
from datetime import datetime
import numpy as np
from os.path import join
from pathlib import Path
from io import UnsupportedOperation

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder

from fishing_game_core.widgets import Boat, TimeBoard, Stats, FishingDerby, Fish
from fishing_game_core.communicator import Communicator
from fishing_game_core.shared import SettingLoader
from fishing_game_core.player_utils import Player
from fishing_game_core.sequences import Sequences
from fishing_game_core.shared import TYPE_TO_SCORE

home = str(Path.home())


class Fishes(SettingLoader):
    def __init__(self):
        super().__init__()
        self.seq_types_fishes = None
        self.observations_sequence = None
        self.main_widget = None
        self.fishes = {}

    def init_fishes(self):
        """
        Initialize fishes and their parameters
        :return:
        """

        # Generate fishes exactly according to the custom specification.
        self.fishes.clear()
        init_fishes = self.observations_sequence['init_fishes']
        for i in range(len(init_fishes)):
            init_x,init_y = init_fishes[str(i)]['init_pos']
            score = init_fishes[str(i)]['score']
            obs_seq = self.observations_sequence['sequence'][str(i)]
            name = "fish"+str(i)
            # Get the right fish type from the score.
            type_fish = None
            for key, value in TYPE_TO_SCORE.items():
                if value == score:
                    type_fish = key
            fish = Fish(init_state=(init_x, init_y),
                        type_fish=type_fish,
                        name=name,
                        observations_sequence=obs_seq,
                        settings=self.settings)
            self.main_widget.ids.fish_layout.add_widget(fish)
            self.fishes[name] = fish

class PrintScoresAbstract:
    def __init__(self):
        self.time = 0
        self.total_time = 0
        self.main_widget = None
        self.players = {}


class PrintScore2Players(PrintScoresAbstract):
    def print_score(self):
        if hasattr(self, 'latest_msg') and self.latest_msg is not None and self.latest_msg['search_time'] is not None:
            search_time = self.latest_msg['search_time']
            print("Elapsed time:", str(self.time) + '/' + str(self.total_time),
              "s\tScore:", self.players[0].score - self.players[1].score, '\tSearch time:', '%.2E' % search_time)
            return
        print("Elapsed time:", str(self.time) + '/' + str(self.total_time),
              "s\tScore:", self.players[0].score - self.players[1].score)


class PrintScore1Player(PrintScoresAbstract):
    def print_score(self):
        print("Elapsed time:", str(self.time) + '/' + str(self.total_time),
              "s\tScore:", self.players[0].score)


class GamesWithBoats:
    def __init__(self):
        self.settings = None
        self.main_widget = None
        self.players = None

    def introduce_boats_to_screen(self, n_boats):
        """
        Introduce and draw the boats on the screen
        :type n_boats: int. Number of boats to draw.
        :return:
        """
        colors = [[0, 0.5, 0, 1], [1, 0, 0, 1]]
        space_subdivisions = 20
        for i in range(1, n_boats + 1):
            if not hasattr(self, 'observations_sequence'): # sanity check
                raise Exception('wrong settings specification for boats...')
            init_players = self.observations_sequence['init_players']
            init_pos = init_players[str(i-1)]
            init_pos_x_boat = init_pos[0]
            init_pos_y_hook = init_pos[1]
            boat = Boat(init_pos_x_boat, space_subdivisions=space_subdivisions,
                        source=f"fishing_game_core/images/fishing{i}.png",
                        init_hook=init_pos_y_hook)
            boat.line_rod.color = colors[i - 1]
            self.main_widget.ids.boats_layout.add_widget(boat)
            self.main_widget.ids.hooks_layout.add_widget(boat.hook)
            self.main_widget.ids.line_rods_layout.add_widget(boat.line_rod)
            self.players[i - 1].boat = boat


class FishingDerbyApp(App, SettingLoader, Communicator):
    def __init__(self):
        App.__init__(self)
        SettingLoader.__init__(self)
        Communicator.__init__(self)

        # Use the main kivy file to draw the board
        Builder.load_file('fishing_game_core/main.kv')

        # Create class variables and set default values
        self.fishes = {}  # Dictionary of fishes
        self._cnt_steps = 0  # Count of the number of steps taken so far
        self.move_x = []  # Next moves of the fishes in the x axis
        self.move_y = []  # Next moves of the fishes in the y axis
        self.action = "stay"  # Actions received from player
        self.time = 0  # Seconds since start
        self.total_time = 60  # Total time of the game
        self.players = []  # Players list
        self.main_widget = None  # Main widget of the game
        self.time_board = None  # Time board widget
        # PID of the player loop in order to be able to kill it when the game is over
        self.player_loop_pid = None
        self.observations_sequence = None
        self.update_scheduled = None
        self.timer_scheduled = None

    # Steps counter is a number that goes from 0 to frames_per_action
    """
    @property
    def cnt_steps(self):
        frames_per_action = 10
        return self._cnt_steps % frames_per_action

    @cnt_steps.setter
    def cnt_steps(self, val):
        self._cnt_steps = val
    """

    def set_player_loop_pid(self, pid):
        self.player_loop_pid = pid

    def create_players(self):
        """Always 2 players, not necessarily 2 boats"""
        self.players = [Player(), Player()]

    def update(self, dt):
        raise NotImplementedError

    def init_clock(self):
        """
        Initialize the timer
        :return:
        """
        n_seq = self.observations_sequence["params"]["n_seq"]
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

    def new_action(self, msg):
        """
        Assign the new action coming from the message
        :param msg: dict. Message coming from the receiver.
        :return:
        """
        self.action = msg["action"]

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
            self.move_x += [move_x / self.settings.frames_per_action]
            self.move_y += [move_y / self.settings.frames_per_action]
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

            if boat.has_fish is not None and boat.hook.position.y == 19:
                self.main_widget.finish_pulling_fish(player_number)

    def load_observations(self):
        """
        Load the observations file stated in the settings
        :return:
        """
        try:
            sequences = Sequences()
            sequences.load(self.settings.observations_file)
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
        self._cnt_steps += 1

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

    def build(self):
        """Initialize the Kivy screen"""
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

        self.update_scheduled = Clock.schedule_interval(
            self.update, 1.0 / self.settings.frames_per_second)

        # Kivy receives main widget and draws it
        return self.main_widget


class FishingDerbyHumanApp(FishingDerbyApp, Fishes, PrintScore1Player, GamesWithBoats):
    def __init__(self):
        super().__init__()

        # Keyboard events
        self._keyboard = None
        self.last_action = None

    def update_clock(self, dl):
        super().update_clock(dl)
        self.print_score()

    def _keyboard_closed(self):
        self._keyboard.unbind(
            on_key_down=self._key_down_function, on_key_up=self._key_up_function)
        self._keyboard = None

    def _key_down_function(self, keyboard, key_code, text, modifiers):
        self.last_action = key_code[1] if key_code[1] in [
            'up', 'down', 'right', 'left'] else 'stay'

    def _key_up_function(self, keyboard, key_code):
        self.last_action = 'stay'

    def update_specific(self, msg):
        msg = {"action": self.last_action}
        self.new_action(msg)

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

        # Attach the keyboard
        self._keyboard = self.main_widget.keyboard
        self._keyboard.bind(on_key_down=self._key_down_function,
                            on_key_up=self._key_up_function)

        # Kivy receives main widget and draws it
        return self.main_widget

    def update(self, dt):
        if self._cnt_steps % self.settings.frames_per_action == 0 and self._cnt_steps > 0:
            # Check if a fish is to be caught by any of the players
            self.check_fishes_caught()

            # Check if game is about to timeout
            if self.time >= self.total_time:
                self.main_widget.game_over = True

            self.send_state_or_display_stats()
            self.fishes_next_move()

        self.update_fishes_position_and_increase_steps()

        self.execute_action()

    def init_specific(self):
        self.init_fishes()
        self.introduce_boats_to_screen(1)

    def execute_action(self):
        if self.players[0].boat.has_fish:
            self.main_widget.act("up", player=0)
        else:
            self.main_widget.act(self.action, player=0)