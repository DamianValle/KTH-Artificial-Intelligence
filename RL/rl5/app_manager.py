import random
from pathlib import Path

import numpy as np
from datetime import datetime
import json
from io import UnsupportedOperation
from os.path import join

from kivy.app import App
from kivy.clock import Clock
# from kivy.core.window import Window
from kivy.lang import Builder

from communicator import Communicator
from shared import SettingLoader
from widgets import Fish, FishingDerby, GreenDiver, TimeBoard, Stats, JellySmile

from position import Position
from headless_utils import Diver, DiverModel, Player, Fishes, PrintScore1Player
from headless_utils import Fish as FishHeadless
from headless_utils import JellySmile as JellySmileHeadless

home = str(Path.home())


class FishingDerbyRLApp(App, SettingLoader, Communicator, PrintScore1Player):
    def __init__(self, headless=True):
        SettingLoader.__init__(self)
        Communicator.__init__(self)
        # self.show_every_n_episodes = 10
        self.headless = headless
        if not self.headless:
            super().__init__()

        self.jellys = {}
        self.p1_rl_model = None
        self.king_fish = None

        self.state2ind = None
        self.ind2state = None

        self.actions = None
        self.allowed_moves = None
        self.actions2ind = None  # ?
        self.exploration = True

        self.policy = None
        self.episode_len_count = 0
        self.episode_len = None
        self.game_over = False

        # Create class variables and set default values
        self.king_fish = None
        self.fishes = {}  # Dictionary of fishes
        self._cnt_steps = 0  # Count of the number of steps taken so far
        self.move_x = []  # Next moves of the fishes in the x axis
        self.move_y = []  # Next moves of the fishes in the y axis
        self.action = "stay"  # Actions received from player
        self.time = 0  # Seconds since start
        self.total_time = 60  # Total time of the game
        self.player = None
        self.time_board = None  # Time board widget
        # PID of the player loop in order to be able to kill it when the game is over
        self.player_loop_pid = None
        self.models = None
        self.update_scheduled = None
        self.timer_scheduled = None
        self.space_subdivisions = 10
        self.frames_per_action = 10
        self.fishderby = None  # Main widget of the game
        self.n_jelly = 0
        if not self.headless:
            Builder.load_file('main.kv')

    # Steps counter is a number that goes from 0 to frames_per_action
    @property
    def cnt_steps(self):
        return self._cnt_steps % self.frames_per_action

    @cnt_steps.setter
    def cnt_steps(self, val):
        self._cnt_steps = val

    def set_player_loop_pid(self, pid):
        self.player_loop_pid = pid

    def create_player(self):
        """Always 1 player, that is 1 boat"""
        self.player = Player()

    def check_fish_near(self, boat):
        """
        Catch a random fish that is on the same position as the boat if possible
        :param boat: Boat. It must not have a caught fish.
        :return:
        """
        inds = np.random.permutation(len(self.fishes))
        keys = list(self.fishes.keys())
        for f in inds:
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
        msg = {"game_over": self.game_over}
        if self.game_over:
            self.sender(msg)
            if not self.headless:
                self.display_stats()
                self.update_scheduled.cancel()
                # self.headless_thread.join()
            return False

        self.sender(msg)

        return True

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

    def introduce_diver(self, state2ind):
        space_subdivisions = self.space_subdivisions
        if self.headless:
            diver = Diver(self.settings.init_pos_diver,
                          space_subdivisions=space_subdivisions,
                          states=state2ind,
                          stoch=self.settings.randomness)
        else:
            diver = GreenDiver(self.settings.init_pos_diver,
                               space_subdivisions=space_subdivisions,
                               source=f"images/scuba.png",
                               states=state2ind,
                               stoch=self.settings.randomness)
            self.main_widget.ids.diver_layout.add_widget(diver)
        self.player.diver = diver

    def init_states(self):
        subdivisions = self.space_subdivisions
        state2ind = {}
        ind2state = {}
        state = 0
        for i in range(subdivisions):
            for j in range(subdivisions):
                state2ind[state] = (i, j)
                ind2state[(i, j)] = state
                state += 1
        self.state2ind = state2ind
        self.ind2state = ind2state

    def init_actions(self):
        self.actions = {
            "left": (-1, 0),
            "right": (1, 0),
            "down": (0, -1),
            "up": (0, 1),
            "stay": (0, 0)
        }
        self.actions2ind = {
            "left": 0,
            "right": 1,
            "down": 2,
            "up": 3,
            "stay": 4
        }

    def receive_action_from_player(self):
        msg = self.receiver()
        self.exploration = msg["exploration"]
        if self.exploration:
            self.new_action(msg)
        else:
            self.policy = msg["policy"]
            if not self.headless:
                self.try_bind_diver_position()
                self.init_clock()

    def update_headless(self, dt):
        if self.headless:
            if self.exploration:
                self.receive_action_from_player()
                if self.exploration:
                    self.modify_action(noise=self.settings.randomness)
                    self.act_simulation(self.action)
            else:
                if self.cnt_steps == 0:
                    current_state = self.player.diver.position.x, self.player.diver.position.y
                    self.action = self.policy[current_state]
                    self.modify_action(noise=self.settings.randomness)

                if self._cnt_steps == 0 or self.cnt_steps != 0:
                    self.act(self.action)
                self._cnt_steps += 1

                if self.cnt_steps == 0:
                    self.check_king_fish_caught()
                    self.check_jellyfish_touched()
                    if self.time >= self.total_time:
                        self.game_over = True
                    if self._cnt_steps >= self.episode_len:
                        self.game_over = True
                    self.send_state_or_display_stats()

                self.time += 1.0 / self.settings.frames_per_second

    def update(self, dt):
        if not self.headless:
            if self.exploration:
                self.receive_action_from_player()
                if self.exploration:
                    self.modify_action(noise=self.settings.randomness)
                    self.act_simulation(self.action)
            else:
                if self.cnt_steps == 0:
                    current_state = self.player.diver.position.x, self.player.diver.position.y
                    self.action = self.policy[current_state]
                    self.modify_action(noise=self.settings.randomness)

                if self._cnt_steps == 0 or self.cnt_steps != 0:
                    self.act(self.action)
                self._cnt_steps += 1

                if self.cnt_steps == 0:
                    self.check_king_fish_caught()
                    self.check_jellyfish_touched()
                    if self.time >= self.total_time:
                        self.game_over = True
                    if self._cnt_steps >= self.episode_len * self.frames_per_action:
                        self.game_over = True

                    self.send_state_or_display_stats()

    def init_jellyfishes(self):
        pos_x = self.settings.jelly_x
        pos_y = self.settings.jelly_y
        for n, (x, y) in enumerate(zip(pos_x, pos_y)):
            if not self.headless:
                jelly = JellySmile(position=(x, y),
                                   space_subdivisions=self.space_subdivisions,
                                   score=self.settings.rewards[1 + n])
                self.main_widget.ids.jelly_layout.add_widget(jelly)
            else:
                jelly = JellySmileHeadless(
                    position=(x, y),
                    space_subdivisions=self.space_subdivisions,
                    score=self.settings.rewards[1 + n])

            self.jellys["jelly" + str(n)] = jelly

    def init_king_fish(self):
        posx, posy = self.settings.pos_king
        score = self.settings.rewards[0]
        name = "king_fish"
        if self.headless:
            fish = FishHeadless(init_state=(posx, posy),
                                type_fish="bowie",
                                name=name,
                                settings=self.settings,
                                score=score)
        else:
            fish = Fish(init_state=(posx, posy),
                        type_fish="bowie",
                        name=name,
                        settings=self.settings,
                        score=score)
            self.main_widget.ids.fish_layout.add_widget(fish)
        self.king_fish = fish

    def check_jellyfish_touched(self):
        diver = self.player.diver
        for key in self.jellys.keys():
            if self.jellys[key].position == diver.position:
                self.player.score += self.jellys[key].score
                self.jellys[key].touched = True
                if not self.headless:
                    self.jellys[key].source = 'images/jelly_hurt.png'

    def check_king_fish_caught(self):
        """
        For every boat in the game, do one of:
        1) if no fish is caught by it, check whether any can be caught
        2) if a fish has been caught and the player is at the surface, finish pulling the rod
        :return:
        """
        diver = self.player.diver
        if diver.has_fish is None:
            self.check_king_fish_near(diver)
            if self.king_fish.caught:
                self.king_fish_caught = True
                self.player.score += 100
                self.game_over = True

        elif diver.has_fish is not None:
            self.king_fish_caught = True
            self.player.score += 100
            self.game_over = True

    def check_king_fish_near(self, diver):
        """
        Catch a random fish that is on the same position as the boat if possible
        :param diver: Diver. It must not have a caught fish.
        :return:
        """
        if self.king_fish.position == diver.position:
            self.king_fish.caught = True

    def act_simulation(self, action):
        """
        Function that simulates the reward given an action and a state
        without the need of displaying it
        :param action:
        :return:
        """
        reward, final_state = self.step(action)
        self.episode_len_count += 1
        if final_state or self.episode_len_count >= self.episode_len:
            self.send_state(reward, end_episode=True)
            # print("I caught fish {}".format(self.n_jelly))
            x, y = self.settings.init_pos_diver
            self.player.diver.position.set_x(x)
            self.player.diver.position.set_y(y)
            self.episode_len_count = 0
            self.n_jelly = 0
        else:
            self.send_state(reward, end_episode=False)
        return None

    def next_state(self, state, action):
        action_tuple = self.actions[action]
        next_state = (state[0] + action_tuple[0], state[1] + action_tuple[1])
        return next_state

    def step(self, action):
        ind_action = self.actions2ind[self.action]
        current_state = self.player.diver.position.x, self.player.diver.position.y
        ind_state = self.ind2state[current_state]
        if not self.player.diver.model[ind_state, ind_action]:
            reward = -100
            final_state = False
            return reward, final_state
        else:
            next_state_x, next_state_y = self.next_state(current_state, action)
            next_state = next_state_x, next_state_y
            self.player.diver.position.set_x(next_state_x)
            self.player.diver.position.set_y(next_state_y)

        reward, final_state = self.compute_reward(next_state)
        return reward, final_state

    def compute_reward(self, next_state):
        next_state_x, next_state_y = next_state
        reward = self.settings.rewards[-1]  #changed from 0....
        final_state = False
        for jelly in range(len(self.jellys)):
            if next_state_x == self.settings.jelly_x[
                    jelly] and next_state_y == self.settings.jelly_y[jelly]:

                reward = self.settings.rewards[1 + jelly]
                self.n_jelly += 1
                break
        if next_state == tuple(self.settings.pos_king):
            reward = self.king_fish.score
            final_state = True
        return reward, final_state

    def send_state(self, reward, end_episode=False):
        """
        Send msg in order to indicate the player we have updated the game. If game has ended, display the stats screen.
        """
        msg = {
            "game_over": self.game_over,
            "state":
            (self.player.diver.position.x, self.player.diver.position.y),
            "reward": reward,
            "end_episode": end_episode
        }

        self.sender(msg)
        return True

    def modify_action(self, noise=1):
        if noise:
            self.noisy_action()
        else:
            self.check_boundaries()

    def check_boundaries(self):
        current_state = self.player.diver.position.x, self.player.diver.position.y
        state = self.ind2state[current_state]
        action = self.actions2ind[self.action]
        if not self.player.diver.model[state, action]:
            self.action = "stay"

    def noisy_action(self):
        current_state = self.player.diver.position.x, self.player.diver.position.y
        s = self.ind2state[current_state]
        action_ind = self.actions2ind[self.action]

        p = self.player.diver.transition_matrix[s, action_ind]
        ind_action = np.random.choice(np.arange(0, 5), p=p)
        noisy_action = list(self.actions2ind.keys())[ind_action]
        self.action = noisy_action

    def act(self, action):
        """
        Update the position of the diver, either left, right, up or down (or stay).
        :param action: String, either 'left', 'right', 'up', 'down' or 'stay'
        :return:
        """
        diver = self.player.diver

        hook_speed = 1.0 / self.frames_per_action

        if action == 'stay':
            pass
        else:
            if action == 'left':
                # 'left'
                self.move_diver_x(diver, -hook_speed)
            elif action == 'right':
                # 'right'
                self.move_diver_x(diver, hook_speed)
            elif action == 'down':
                # 'down'
                self.move_diver_y(diver, -hook_speed)
            elif action == 'up':
                # 'up'
                self.move_diver_y(diver, hook_speed)

    @staticmethod
    def move_diver_x(diver, speed):
        diver.position.increase_x(speed)

    @staticmethod
    def move_diver_y(diver, speed):
        diver.position.increase_y(speed)

    # Methods dependent of Kivy
    def init_clock(self):
        """
        Initialize the timer
        :return:
        """
        self.total_time = self.settings.game_time
        self.time_board = TimeBoard(seconds=int(self.total_time))

        self.time_board.pos_hint['center_x'] = 0.5
        if not self.headless:
            self.main_widget.add_widget(self.time_board)

        self.timer_scheduled = Clock.schedule_interval(self.update_clock, 1.0)

    def build(self):
        """Initialize the Kivy screen"""
        # Set sky color
        from kivy.core.window import Window
        Window.clearcolor = 63 / 255, 191 / 255, 191 / 255, 0.3
        # Create main widget
        self.main_widget = FishingDerby(fishes=self.fishes,
                                        player=self.player,
                                        settings=self.settings)
        self.create_player()
        self.init_king_fish()
        self.init_jellyfishes()
        self.init_states()
        self.introduce_diver(self.state2ind)
        self.init_actions()
        self.episode_len = self.settings.episode_len

        self.update_scheduled = Clock.schedule_interval(
            self.update, 1.0 / self.settings.frames_per_second)

        if not self.settings.visualize_exploration:
            # temporarily unbind the diver's position from drawing it for exploration
            self.player.diver.position.unbind(pos_x=self.player.diver.on_state)
            self.player.diver.position.unbind(pos_y=self.player.diver.on_state)

        # import threading
        # self.headless_thread = threading.Thread(target=self.headless_mode)
        # self.headless_thread.start()

        # Kivy receives main widget and draws it
        return self.main_widget

    def headless_mode(self):
        if self.headless:
            self.create_player()
            self.init_king_fish()
            self.init_jellyfishes()
            self.init_states()
            self.introduce_diver(self.state2ind)
            self.init_actions()
            self.episode_len = self.settings.episode_len

        self.time = 0  # Seconds since start
        # Total time of the game
        self.total_time = self.settings.game_time

        while True:
            self.update_headless(1)
            if self.game_over:
                break

        res = self.check_sequence_and_kill_player_control()
        return res

    def update_clock(self, dl):
        """
        Increase the clock by 1 second. If the remaining time is 0, the game is over.
        :param dl: delta-time. Not used.
        :return:
        """
        if self.time_board.seconds == 0:
            self.game_over = True
        else:
            self.time_board.seconds -= 1
            self.time += 1.0

        self.print_score()

    def display_stats(self):
        scores_file = join(home, ".fishing_derby_scores")
        stats = Stats(self.player, self.settings, self.king_fish)
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

    def try_bind_diver_position(self):
        if not self.settings.visualize_exploration:
            # rebind the diver's position for drawing it during simulation
            self.player.diver.position.bind(pos_x=self.player.diver.on_state)
            self.player.diver.position.bind(pos_y=self.player.diver.on_state)

    # Headless mode methods
    def run_headless(self):
        """Initialize the testing environment"""
        #kivy inherited stuff
        if self.headless:
            self.headless_mode()
        else:
            self.run()

    # Tester specific methods
    def print_tester_results(self):
        print("".join([(str(1) if i is True else str(0))
                       for i in self.passes.values()]))

    def check_score_threshold(self):
        return self.player.score >= 100

    def check_sequence_and_kill_player_control(self):
        passed = self.check_score_threshold()
        return passed

    def reset_scores(self):
        self.player.score = 0

    @staticmethod
    def set_seed(seed):
        random.seed(seed)
        np.random.seed(seed)
