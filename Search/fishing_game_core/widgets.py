import os
import random
random.seed(2020)

from kivy.app import App
from kivy.core.window import Window
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, ListProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from fishing_game_core.position import Position


class Boat(Image):
    has_fish = ObjectProperty(None, allownone=True)

    def __init__(self, init_state, source, space_subdivisions, init_hook=None):
        super().__init__(source=source)
        self.position = Position(self, space_subdivisions)
        self.position.set_x(init_state)
        self.line_rod = LineRod(self, space_subdivisions, init_state=init_hook)
        self.hook = Hook(self, self.line_rod, space_subdivisions)
        self.num_fishes_caught = 0

    def on_state(self, obj, val):
        self.pos_hint = {"center_x": self.position.pos_x,
                         "top": 0.98}


class Crab(Image):
    score = StringProperty("00")

    def on_score(self, obj, score):
        score = int(score)
        if score == 0:
            score_str = '00'
        elif 0 < score < 10:
            score_str = '0' + str(score)
        else:
            score_str = str(score)
        self.score = score_str


class Fish(Image):
    orientation = NumericProperty(1.0)
    caught = ObjectProperty(None)

    def __init__(self, init_state, type_fish, name, settings, observations_sequence):
        super().__init__()
        self.type_fish = type_fish
        self.name = name
        self.prev_direction = random.choice(range(8))
        if self.prev_direction in [2, 4, 6]:
            self.orientation = -1
        self.observation = None
        self.observations_sequence = observations_sequence
        self.updates_cnt = 0
        self.source = 'fishing_game_core/images/fish' + str(type_fish) + '.png'
        self.settings = settings
        space_subdivisions = 20
        self.position = Position(self, space_subdivisions)
        self.position.set_x(init_state[0])
        self.position.set_y(init_state[1])
        self.prev_move = None
        from fishing_game_core.shared import TYPE_TO_SCORE
        self.score = TYPE_TO_SCORE[type_fish] # was: self.score = type_fish + 1 if type_fish < 6 else -7
        self.guessed = False

    def next_movement_and_flip_horizontally(self):
        if self.caught is not None:
            return 0, 0

        if self.observations_sequence is None:
            new_direction = self.model.sample(
                previous_state=self.prev_direction)
        else:
            new_direction = self.observations_sequence[self.updates_cnt]
        self.prev_move = new_direction
        self.observation = new_direction

        if new_direction in [3, 5, 7]:
            move_x = 1
            self.orientation = move_x
        elif new_direction in [2, 4, 6]:
            move_x = -1
            self.orientation = move_x
        else:
            move_x = 0

        if new_direction in [0, 4, 5]:
            move_y = 1
        elif new_direction in [1, 6, 7]:
            move_y = -1
        else:
            move_y = 0

        return move_x, move_y

    def attach_hook(self, rod):
        """
        Enforce the center of the fish to be hooked up to the tip of the rod
        :return:
        """
        self.pos_hint = {"center_x": rod.hook.center_x / self.parent.size[0],
                         "center_y": rod.hook.pos[1] / self.parent.size[1]}

    def on_state(self, ins, val):
        self.pos_hint = {"center_x": self.position.pos_x,
                         "center_y": self.position.pos_y}

    def increase_x_y(self, x, y):
        if self.caught is not None:
            self.attach_hook(self.caught)
        else:
            self.position.increase_x(x)
            self.position.increase_y(y)


class Hook(Image):
    def __init__(self, boat, line_rod, space_subdivisions):
        super().__init__()
        self.boat = boat
        self.line_rod = line_rod
        self.position = Position(self, space_subdivisions)
        self.position.set_x(boat.position.x)
        self.position.set_y(line_rod.position.y)

    def on_state(self, *args, **kwargs):
        self.pos_hint = {
            "center_x": self.position.pos_x + 0.0035,
            "center_y": self.position.pos_y
        }


class LineRod(Widget):
    color = ListProperty([0, 0.5, 0, 1])

    def __init__(self, boat, space_subdivisions, init_state=None):
        super().__init__()
        self.boat = boat
        self.position = Position(self, space_subdivisions)
        self.position.set_x(boat.position.x)
        if init_state is None:
            self.position.set_y(space_subdivisions - 1)
        else:
            self.position.set_y(init_state)

    def on_state(self, *args, **kwargs):
        self.size_hint = None, 1.075 - self.position.pos_y
        self.pos_hint = {
            "center_x": self.position.pos_x,
            "top": 1.1
        }


class FishingDerby(FloatLayout):
    sea = ObjectProperty(None)
    game_over = BooleanProperty(False)

    def __init__(self, fishes, players, settings):
        super().__init__()

        # Keyboard events
        self.keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self.keyboard.bind(on_key_down=self._on_keyboard_down)

        self.fishes = fishes
        self.settings = settings
        self.space_subdivisions = 20
        self.frames_per_action = 10
        self.players = players
        self.crabs = []
        self.models = None

        for i in range(len(players)):
            try:
                self.crabs.append(eval("self.ids.crab" + str(i)))
            except AttributeError:
                print("We need a crab for player " + str(i))

    def _keyboard_closed(self):
        self.keyboard.unbind(on_key_down=self._on_keyboard_down)
        self.keyboard = None

    def _on_keyboard_down(self, keyboard, key_code, text, modifiers):
        if key_code[1] == 'escape':
            app = App.get_running_app()
            os.kill(app.player_loop_pid, 9)
            app.stop()
        return True

    def act(self, action, player=0):
        """
        Update the position of the ship and the depth of the hook, either left, right, up or down (or stay).
        :param player: int. index of the boat on which to perform the action
        :param action: String, either 'left', 'right', 'up', 'down' or 'stay'
        :return:
        """
        boat = self.players[player].boat
        adv_boat = self.players[1-player].boat

        hook_speed = 1.0 / self.frames_per_action

        if action == 'left':
            self.move_boat(boat, -hook_speed, adv_boat, self.space_subdivisions)
        elif action == 'right':
            self.move_boat(boat, hook_speed, adv_boat, self.space_subdivisions)
        elif action == 'down':
            self.move_hook(boat, -hook_speed)
        elif action == 'up':
            self.move_hook(boat, hook_speed)
        elif action == 'stay':
            pass

    @staticmethod
    def move_boat(boat, speed, adv_boat, space_subdivisions):
        other_boat = False
        slack = 1.0 / space_subdivisions
        boat_x = boat.position.pos_x
        next_boat_x = (boat_x + speed / space_subdivisions) % 1
        if adv_boat is not None: # then there is an adverserial boat.
            adv_boat_x = adv_boat.position.pos_x
            will_cross = abs(next_boat_x - adv_boat_x) < slack
        else: # no adverserial boat so then clearly no crossing.
            will_cross = False
        if not will_cross: # check they don't cross
            boat.hook.position.increase_x(speed)
            boat.line_rod.position.increase_x(speed)
            boat.position.increase_x(speed)

    @staticmethod
    def move_hook(boat, speed):
        boat.hook.position.increase_y(speed)
        boat.line_rod.position.increase_y(speed)

    def finish_pulling_fish(self, player_number):
        player = self.players[player_number]
        boat = player.boat
        # Update score on the crab
        fish_score = boat.has_fish.score
        player.score += fish_score
        self.update_score(player.score, player_number)

        # Remove the fish
        fish = boat.has_fish
        self.ids.fish_layout.remove_widget(fish)
        del self.fishes[fish.name]
        boat.has_fish = None

        # Increase boat counter
        boat.num_fishes_caught += 1

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


class MinimaxStats(StatsContent):
    def parse_stats_dict_and_add_text(self, stats_dict):
        score = stats_dict["score_p0"] - stats_dict["score_p1"]
        self.text = f"[b]Final score[/b]: {score}\n"
        self.text += f"[b]Player 0 final score[/b]: {stats_dict['score_p0']}\n"
        self.text += f"[b]Player 1 final score[/b]: {stats_dict['score_p1']}\n"
        self.text += f"[b]Number of caught fishes by player 0[/b]: {stats_dict['num_fishes_caught_p0']}\n"
        if "num_fishes_caught_p1" in stats_dict:
            self.text += f"[b]Number of caught fishes by player 1[/b]: " \
                         f"{stats_dict['num_fishes_caught_p1']}"


class ExpectimaxStats(StatsContent):
    parse_stats_dict_and_add_text = MinimaxStats.parse_stats_dict_and_add_text


class Stats(Popup):
    def __init__(self, players, settings, fishes):
        super().__init__()
        self.players = players
        self.settings = settings
        self.background_color = [0, 0, 0, 0]
        self.size_hint = (0.75, 0.75)
        self.pos_hint = {
            "center_x": 0.5,
            "center_y": 0.5
        }
        self.title_size = 32
        self.auto_dismiss = False
        self.fishes_widgets = fishes

    def load(self, stats_dict):
        self.content = BoxLayout(orientation='vertical')
        self.title = "Stats"
        self.content.add_widget(ExpectimaxStats(stats_dict))
        self.content.add_widget(ExitButton())

    def get_stats(self):
        stats = {"score_p0": self.players[0].score, "score_p1": self.players[1].score,
                 "num_fishes_caught_p0": self.players[0].boat.num_fishes_caught}
        if self.players[1].boat is not None:
            stats["num_fishes_caught_p1"] = self.players[1].boat.num_fishes_caught
        return stats


class TimeBoard(FloatLayout):
    seconds = NumericProperty(60)
    text = StringProperty()

    def on_seconds(self, obj, s):
        self.text = f"{s // 60:02d}:{s % 60:02d}"
