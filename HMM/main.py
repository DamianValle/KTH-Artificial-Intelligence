import argparse
import multiprocessing as mp
import os
import signal
import sys

import yaml
from kivy.config import Config

from shared import SettingLoader

import constants



class Settings:
    def __init__(self):
        # Number of divisions of the sea in every axis
        self.space_subdivisions = None
        # Frame rate of the game in seconds per frame
        self.frames_per_second = None
        # Window size is immutable and equal to self.window_scale * (800, 600)
        self.window_scale = None
        # Time threshold
        self.time_threshold = None

    def load_from_dict(self, dictionary):
        """
        Load parameters into settings object from dictionary.
        :param dictionary:
        :return:
        """
        self.frames_per_second = dictionary.get("frames_per_second", 20)
        self.window_scale = dictionary.get("window_scale", 1.0)
        self.time_threshold = dictionary.get("time_threshold", 5e-1)


class Application(SettingLoader):
    def __init__(self):
        SettingLoader.__init__(self)

        # Declaration of class objects
        self.game_controller = None
        self.player_controller = None
        self.settings = None
        self.game_pipe_send = None
        self.game_pipe_receive = None
        self.player_pipe_receive = None
        self.player_pipe_send = None
        self.player_loop = None

    def start(self):
        """
        Start game and player processes
        :return:
        """
        # Initialize game process
        self.game_controller = self.get_app()
        self.game_controller.load_settings(self.settings)
        self.game_controller.set_receive_send_pipes(
            self.game_pipe_receive, self.game_pipe_send)

        # Initialize player process
        self.player_controller = self.get_player_controller()
        self.player_controller.load_settings(self.settings)
        self.player_controller.set_receive_send_pipes(
            self.player_pipe_receive, self.player_pipe_send)

        # Set player loop to use
        self.select_and_launch_player_loop()
        self.start_game()

    def select_and_launch_player_loop(self):
        # Create process
        self.player_loop = mp.Process(
            target=self.player_controller.player_loop, daemon=True)

        # Start process
        self.player_loop.start()

    @staticmethod
    def get_app():
        from app import FishingDerbyHMMApp
        return FishingDerbyHMMApp()

    def start_game(self):
        """
        Starting the game and the parallel processes: player and game.
        :return:
        """
        self.game_controller.set_player_loop(self.player_loop)

        # Start interface
        self.game_controller.run()

        # After closing window wait until the player loop finishes
        # self.player_loop.join()

        sys.exit(0)

    def create_pipes(self):
        """
        Create pipes to allow exchange of data between player and game processes
        :return:
        """
        self.game_pipe_send, self.player_pipe_receive = mp.Pipe()
        self.player_pipe_send, self.game_pipe_receive = mp.Pipe()

    @staticmethod
    def get_player_controller():
        # from player_controller_hmm import PlayerControllerHMM
        from player import PlayerControllerHMM
        pc = PlayerControllerHMM()
        return pc


if __name__ == '__main__':
    # Load the settings from the yaml file
    settings = Settings()
    settings_dictionary = yaml.safe_load(open('settings.yml', 'r'))
    settings_dictionary['time_threshold'] = constants.STEP_TIME_THRESHOLD
    settings.load_from_dict(settings_dictionary)

    # Set window dimensions
    Config.set('graphics', 'resizable', False)
    Config.set('graphics', 'width', str(int(settings.window_scale * 800)))
    Config.set('graphics', 'height', str(int(settings.window_scale * 600)))

    # Start application
    app = Application()
    app.load_settings(settings)
    app.create_pipes()
    app.start()
