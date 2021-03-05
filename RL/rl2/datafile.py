import json
from json import JSONEncoder
import numpy as np


class Datafile:
    def __init__(self,):
        self.data = None
        self.models = None

    def load(self, filename):
        with open(filename, 'r') as f:
            self.data = json.load(f)

    def save(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.data, f, cls=DatafileEncoder)


class ModelsDatafile(Datafile):
    pass


class SequencesDatafile(Datafile):
    pass


class DatafileEncoder(JSONEncoder):
    def default(self, o):
        if type(o) is np.ndarray:
            return o.tolist()