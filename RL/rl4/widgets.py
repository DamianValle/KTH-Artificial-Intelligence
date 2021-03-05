import os
import random

import numpy as np
from kivy.app import App
# from kivy.core.window import Window
from kivy.properties import StringProperty, ObjectProperty, NumericProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from position import PositionGUI

from headless_utils import Diver, DiverModel


class BoxStats(TextInput):
    text = StringProperty()


class GreenDiver(Image):
    has_fish = ObjectProperty(None, allownone=True)

    def __init__(self,
                 init_state,
                 source,
                 space_subdivisions,
                 states,
                 stoch=True):
        super().__init__(source=source)
        self.position = PositionGUI(self, space_subdivisions)
        self.position.set_x(init_state[0])
        self.position.set_y(init_state[1])
        self.model, self.transition_matrix = DiverModel().diver_model(
            states, space_subdivisions, prob_erratic=0.05 if stoch else 0.0)

    def on_state(self, ins, val):
        self.pos_hint = {
            "center_x": self.position.pos_x,
            "center_y": self.position.pos_y
        }


class Fish(Image):
    orientation = NumericProperty(1.0)
    caught = ObjectProperty(None)

    def __init__(self, init_state, type_fish, name, settings, score=10):
        super().__init__()
        self.type_fish = type_fish
        self.name = name
        self.prev_direction = random.choice(range(8))
        if self.prev_direction in [2, 4, 6]:
            self.orientation = -1
        self.observation = None
        self.updates_cnt = 0
        self.source = 'images/fish' + str(type_fish) + '.png'
        self.settings = settings
        space_subdivisions = 10
        self.position = PositionGUI(self, space_subdivisions)
        self.position.set_x(init_state[0])
        self.position.set_y(init_state[1])
        self.prev_move = None
        self.score = score

    def on_state(self, ins, val):
        self.pos_hint = {
            "center_x": self.position.pos_x,
            "center_y": self.position.pos_y
        }


class Jellyfish(Image):
    def __init__(self, position=None, space_subdivisions=None, score=0):
        super().__init__()
        self.source = 'images/jelly_smile.png'
        self.position = PositionGUI(self, space_subdivisions)
        self.position.set_x(position[0])
        self.position.set_y(position[1])
        self.score = score
        self.touched = False

    def on_state(self, ins, val):
        self.pos_hint = {
            "center_x": self.position.pos_x,
            "center_y": self.position.pos_y
        }


class JellySmile(Jellyfish):
    pass


class JellyHurt(Jellyfish):
    pass


class FishingDerby(FloatLayout):
    sea = ObjectProperty(None)

    def __init__(self, fishes, player, settings):
        super().__init__()
        from kivy.core.window import Window
        # Keyboard events
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

        self.fishes = fishes
        self.settings = settings
        self.space_subdivisions = 10
        self.frames_per_action = 10
        self.player = player
        self.crabs = []
        self.jellies = {}

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'escape':
            app = App.get_running_app()
            os.kill(app.player_loop_pid, 9)
            app.stop()
        return True

    def update_score(self, score, player):
        try:
            self.crabs[player].score = str(score)
        except IndexError:
            print("Can't write score to non existing crab")


class ExitButton(Button):
    pass


class StatsContent(ScrollView):
    text = StringProperty("")

    def __init__(self, stats_dict):
        super().__init__()
        self.parse_stats_dict_and_add_text(stats_dict)


class RLStats(StatsContent):
    def parse_stats_dict_and_add_text(self, stats_dict):
        score = stats_dict["score"]
        self.text = f"[b]Final score[/b]: {score}\n"
        self.text += f"[b]King Fish caught[/b]: {stats_dict['fish_caught']}\n"


class Stats(Popup):
    def __init__(self, player, settings, fish):
        super().__init__()
        self.players = player
        self.settings = settings
        self.background_color = [0, 0, 0, 0]
        self.size_hint = (0.75, 0.75)
        self.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        self.title_size = 32
        self.auto_dismiss = False
        self.fishes_widgets = fish

    def load(self, stats_dict):
        self.content = BoxLayout(orientation='vertical')
        self.title = "Reinforcement Learning Stats"
        self.content.add_widget(RLStats(stats_dict))
        self.content.add_widget(ExitButton())

    def get_stats(self):
        stats = {
            "score": self.players.score,
            "fish_caught": self.fishes_widgets.caught
        }
        if self.settings.player_type == "ai_hmm":
            stats["fishes"] = [(f.source, f.guessed)
                               for f in self.fishes_widgets.values()]
        elif self.settings.player_type == "ai_minimax" or self.settings.player_type == "ai_minimax":
            stats["num_fishes_caught_p0"] = self.players[
                0].boat.num_fishes_caught
            stats["num_fishes_caught_p1"] = self.players[
                1].boat.num_fishes_caught
            stats["tree_depth"] = self.settings.tree_depth
        return stats


class TimeBoard(FloatLayout):
    seconds = NumericProperty(60)
    text = StringProperty()

    def on_seconds(self, obj, s):
        self.text = f"{s // 60:02d}:{s % 60:02d}"
