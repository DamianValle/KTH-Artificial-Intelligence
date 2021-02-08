import random

from kivy.properties import BooleanProperty
from kivy.properties import NumericProperty
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView

from position import Position


class FishingDerby(FloatLayout):
    sea = ObjectProperty(None)
    game_over = BooleanProperty(False)

    def __init__(self, fishes, players, settings):
        super().__init__()

        self.fishes = fishes
        self.settings = settings
        self.players = players
        self.crabs = []

        fl = FloatLayout()
        for i in range(len(players)):
            al = AnchorLayout(anchor_x="left", anchor_y="bottom")
            crab = GreenCrab(score="00")
            al.add_widget(crab)
            fl.add_widget(al)
            self.crabs.append(crab)

            al = AnchorLayout(anchor_x="right", anchor_y="bottom")
            crab = RedCrab(score="")
            al.add_widget(crab)
            fl.add_widget(al)

        self.add_widget(fl)

    @staticmethod
    def sample_state():
        s = 20  # Space subdivisions
        range_x = [0.0 + x * 1.0 / s for x in range(s + 1)]
        range_y = [0.0 + x * 1.0 / s for x in range(s + 1)]
        random_x = random.randint(0, s - 1)
        random_y = random.randint(0, s - 1)
        init_x = range_x[random_x]
        init_y = range_y[random_y]
        if init_x <= 0.3:
            init_x = 0.3
        elif init_x >= 0.7:
            init_x = 0.7
        if init_y <= 0.3:
            init_y = 0.3
        elif init_y >= 0.7:
            init_y = 0.7
        return init_x, init_y, random_x, random_y

    def update_score(self, score, player):
        try:
            self.crabs[player].score = str(score)
        except IndexError:
            print("Can't write score to non existing crab")


class TimeBoard(FloatLayout):
    seconds = NumericProperty(60)
    text = StringProperty()

    def __init__(self, seconds):
        super().__init__()
        self.bind(seconds=lambda _, s: self.seconds_f(s))
        self.seconds = seconds

    def seconds_f(self, s):
        self.text = f"{s // 60:02d}:{s % 60:02d}"


class ExitButton(Button):
    pass


class StatsContent(ScrollView):
    text = StringProperty("")

    def __init__(self, stats_dict):
        super().__init__()
        self.parse_stats_dict_and_add_text(stats_dict)


class HMMStats(StatsContent):

    def parse_stats_dict_and_add_text(self, stats_dict):
        bl = BoxLayout(orientation='horizontal')
        for (source, guessed) in stats_dict["fishes"]:
            hl = BoxLayout(orientation='vertical')
            hl.add_widget(
                Image(source=source, size_hint=(None, None), size=(32, 32)))
            if guessed:
                hl.add_widget(Image(source="images/correct.png",
                                    size_hint=(None, None), size=(32, 32)))
            else:
                hl.add_widget(Image(source="images/wrong.png",
                                    size_hint=(None, None), size=(32, 32)))
            bl.add_widget(hl)
        self.ids.layout.add_widget(bl)
        score = stats_dict["score_p0"]
        self.text = f"[b]Final score[/b]: {score}\n"
        rate = str(stats_dict['guessed']) + "/" + str(stats_dict['guessed'] + stats_dict['non_guessed'])
        self.text += f"[b]Guessed fishes[/b]: {rate}\n"


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
        self.guessed = 0
        self.non_guessed = 0

    def load(self, stats_dict):
        self.content = BoxLayout(orientation='vertical')
        self.title = "HMM Stats"
        self.content.add_widget(HMMStats(stats_dict))
        self.content.add_widget(ExitButton())

    def get_stats(self):
        self.count_guess()
        stats = {"score_p0": self.players[0].score, "guessed": self.guessed, "non_guessed": self.non_guessed,
                 "fishes": [(f.source, f.guessed) for f in self.fishes_widgets.values()]}
        return stats

    def count_guess(self):
        for f in self.fishes_widgets.values():
            if f.guessed:
                self.guessed += 1
            else:
                self.non_guessed += 1


class Crab(Image):
    score = StringProperty("00")

    def __init__(self, score):
        super().__init__()
        self.bind(score=lambda _, s: self.score_f(s))
        self.score = score

    def score_f(self, score):
        score_str = ""
        try:
            if score == 0:
                score_str = '00'
            elif 0 < score < 10:
                score_str = '0' + str(int(score))
        except TypeError:
            score_str = str(score)
        self.score = score_str


class GreenCrab(Crab):
    def __init__(self, score):
        super().__init__(score=score)
        self.source = 'images/crab1.png'


class RedCrab(Crab):
    def __init__(self, score):
        super().__init__(score=score)
        self.source = 'images/crab2.png'


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
        self.source = 'images/fish' + str(type_fish) + '.png'
        self.settings = settings
        self.position = Position(self, 20)
        self.position.set_x(init_state[0])
        self.position.set_y(init_state[1])
        self.prev_move = None
        self.score = type_fish + 1 if type_fish < 6 else -7
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
