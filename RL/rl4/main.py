import argparse
import multiprocessing as mp
import sys

import yaml
from kivy import Config

from shared import SettingLoader


class Settings:
    def __init__(self):
        # Player mode, either 'human' or 'ai_rl'
        self.player_type = None
        # Frame rate of the game in seconds per frame
        self.frames_per_second = None
        # Window size is immutable and equal to self.window_scale * (800, 600)
        self.window_scale = None
        # Duration of the game in seconds
        self.game_time = None
        # Initial position of diver
        self.init_pos_diver = None
        # Jellyfishes x position
        self.jelly_x = None
        # Jellyfishes y position
        self.jelly_y = None
        # Rewards for bumping [golden_fish, jellyfish, step]
        self.rewards = None
        # Position of the king fish
        self.pos_king = None
        # Stochasticity
        self.randomness = None
        # Episode length
        self.episode_len = None
        # Max Episodes
        self.episode_max = None
        # Visualize exploration
        self.visualize_exploration = None
        # Headless
        self.headless = None
        # Seed
        self.seed = None
        # Learning rate
        self.alpha = 0
        # Discount rate
        self.discount = 0
        # epsilon initial
        self.epsilon_initial = 1
        # epsilon final
        self.epsilon_final = 1
        # annealing timesteps
        self.annealing_timesteps = 10000
        # threshold
        self.threshold = 1e-6

    def load_from_dict(self, dictionary):
        """
        Load parameters into settings object from dictionary.
        :param dictionary:
        :return:
        """
        self.player_type = dictionary.get("player_type")
        self.frames_per_second = dictionary.get("frames_per_second", 20)
        self.init_pos_diver = dictionary.get('init_pos_diver', [1, 19])
        self.jelly_x = dictionary.get("jelly_x", [2, 2, 2, 2, 2])
        self.jelly_y = dictionary.get("jelly_y", [2, 2, 2, 2, 2])
        self.rewards = dictionary.get("rewards", [1, -1, -1, -1, -1])
        self.pos_king = dictionary.get("pos_king", [0.5, 0.5])
        self.window_scale = dictionary.get("window_scale", 1.0)
        self.game_time = dictionary.get("time", 120)
        self.randomness = dictionary.get("stoch", True)
        self.episode_len = dictionary.get("episode_len", 100)
        self.episode_max = dictionary.get("episode_max", 1000)
        self.visualize_exploration = dictionary.get("visualize_exploration",
                                                    False)
        self.headless = dictionary.get("headless")
        self.seed = dictionary.get("seed", None)
        self.alpha = dictionary.get("alpha", 0)
        self.gamma = dictionary.get("gamma", 0)
        self.threshold = dictionary.get("threshold", 1e-6)
        self.threshold = float(self.threshold)
        self.epsilon_final = dictionary.get("epsilon_final", 1)
        self.epsilon_initial = dictionary.get("epsilon_initial", 0.2)
        self.annealing_timesteps = dictionary.get("annealing_timesteps", 10000)


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
        self.game_controller = self.get_app(self.settings.headless)
        self.game_controller.load_settings(self.settings)
        self.game_controller.set_receive_send_pipes(self.game_pipe_receive,
                                                    self.game_pipe_send)
        if self.settings.seed is not None:
            self.game_controller.set_seed(self.settings.seed)  #507 episodes

        # Initialize player process
        self.player_controller = self.get_player_controller()
        self.player_controller.load_settings(self.settings)
        self.player_controller.set_receive_send_pipes(self.player_pipe_receive,
                                                      self.player_pipe_send)

        # Set player loop to use
        self.select_and_launch_player_loop()
        self.start_game()

    def select_and_launch_player_loop(self):
        # Create process
        self.player_loop = mp.Process(
            target=self.player_controller.player_loop)

        # Start process
        self.player_loop.start()

    @staticmethod
    def get_app(headless=True):
        # from app import FishingDerbyRLApp
        from app_manager import FishingDerbyRLApp

        a = FishingDerbyRLApp(headless=headless)
        return a

    def get_player_controller(self):
        if self.settings.player_type == "human":
            from player import PlayerControllerHuman
            pc = PlayerControllerHuman()
        elif self.settings.player_type == "ai_rl":
            # from player import PlayerControllerRL
            from player import PlayerControllerRL
            pc = PlayerControllerRL()
        elif self.settings.player_type == "random":
            from player import PlayerControllerRandom
            pc = PlayerControllerRandom()
        else:
            raise NotImplementedError
        return pc

    def start_game(self):
        """
        Starting the game and the parallel processes: player and game.
        :return:
        """
        self.game_controller.set_player_loop_pid(self.player_loop.pid)

        # Start graphical interface
        self.game_controller.run_headless()
        # self.game_controller.run()

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


if __name__ == '__main__':
    # Arguments parsing
    arg_parser = argparse.ArgumentParser(
        description="Run the fishing derby KTH app")
    arg_parser.add_argument("config_file", type=str, help="Configuration file")
    args = arg_parser.parse_args()

    # Load the settings from the yaml file
    settings = Settings()
    settings_dictionary = yaml.safe_load(open(args.config_file, 'r'))
    settings.load_from_dict(settings_dictionary)

    # Set window dimensions
    if not settings.headless:
        Config.set('graphics', 'resizable', False)
        Config.set('graphics', 'width', str(int(settings.window_scale * 800)))
        Config.set('graphics', 'height', str(int(settings.window_scale * 600)))

    # Start application
    app = Application()
    app.load_settings(settings)
    app.create_pipes()
    app.start()
