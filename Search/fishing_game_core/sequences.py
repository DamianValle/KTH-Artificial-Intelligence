from fishing_game_core.datafile import SequencesDatafile


class Sequences:
    def __init__(self):
        self.data = {}
        self.models = None

    def load(self, filename):
        datafile = SequencesDatafile()
        datafile.load(filename)
        self.data = datafile.data
        return self
