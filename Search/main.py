import argparse
import multiprocessing as mp
import sys

import yaml
from kivy.config import Config

from fishing_game_core.shared import SettingLoader


class Settings:
    def __init__(self):
        # File from where to load observations. If unavailable, generate sequence from model.
        self.observations_file = None
        # Player mode, either 'human' or 'ai_minimax'
        self.player_type = None
        # Frame rate of the game in frame per seconds
        self.frames_per_second = 20
        # Window size is immutable and equal to self.window_scale * (800, 600)
        self.window_scale = 1.0
        # Time threshold
        self.time_threshold = 75*1e-3
        # Space subdivisions
        self.space_subdivisions = 20
        # Number of frames before an action is executed
        self.frames_per_action = 10

    def load_from_dict(self, dictionary):
        """
        Load parameters into settings object from dictionary.
        :param dictionary:
        :return:
        """
        self.observations_file = dictionary.get("observations_file")
        self.player_type = dictionary.get("player_type", "human")


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
        self.player_controller.set_receive_send_pipes(self.player_pipe_receive, self.player_pipe_send)

        # Set player loop to use
        self.select_and_launch_player_loop()
        if self.settings.player_type == 'ai_minimax':
            self.game_controller.set_seed(120283473)
        self.start_game()

    def select_and_launch_player_loop(self):
        # Create process
        self.player_loop = mp.Process(
            target=self.player_controller.player_loop)

        # Start process
        self.player_loop.start()

    def get_app(self):
        player_type = self.settings.player_type
        if player_type == "human":
            from fishing_game_core.app import FishingDerbyHumanApp
            app_o = FishingDerbyHumanApp()
        elif player_type == "ai_minimax":
            from app import FishingDerbyMinimaxApp
            app_o = FishingDerbyMinimaxApp()
        else:
            raise AttributeError("Player type not understood")

        return app_o

    def start_game(self):
        """
        Starting the game and the parallel processes: player and game.
        :return:
        """
        self.game_controller.set_player_loop_pid(self.player_loop.pid)

        # Start graphical interface
        self.game_controller.run()

        # After closing window wait until the player loop finishes
        self.player_loop.join()

        sys.exit(0)

    def create_pipes(self):
        """
        Create pipes to allow exchange of data between player and game processes
        :return:
        """
        self.game_pipe_send, self.player_pipe_receive = mp.Pipe()
        self.player_pipe_send, self.game_pipe_receive = mp.Pipe()

    def get_player_controller(self):
        if self.settings.player_type == "ai_minimax":
            from player import PlayerControllerMinimax
            pc = PlayerControllerMinimax()
        elif self.settings.player_type == "human":
            from player import PlayerControllerHuman
            pc = PlayerControllerHuman()
        else:
            raise AttributeError(
                "Parameter " + self.settings.player_type + " not understood")
        return pc


if __name__ == '__main__':
    # Arguments parsing
    arguments_parser = argparse.ArgumentParser(
        description="Run the fishing derby KTH app")
    arguments_parser.add_argument("config_file", type=str,
                                  help="Configuration file")
    args = arguments_parser.parse_args()

    # Load the settings from the yaml file
    settings = Settings()
    settings_dictionary = yaml.safe_load(open(args.config_file, 'r'))
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
