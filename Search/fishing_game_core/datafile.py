import json


class Datafile:
    def __init__(self, ):
        self.data = None
        self.models = None

    def load(self, filename):
        with open(filename, 'r') as f:
            self.data = json.load(f)


class ModelsDatafile(Datafile):
    pass


class SequencesDatafile(Datafile):
    pass
