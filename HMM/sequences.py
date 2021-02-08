from datafile import SequencesDatafile


class Sequences:
    def __init__(self, generator=None):
        self.data = {}
        self.models = None
        if generator:
            self.generator = generator()
            self.generator.load_data(self.data)

    def associate_models(self, models):
        self.models = models
        self.generator.load_models(self.models)

    def load(self, input_stream):
        datafile = SequencesDatafile()
        datafile.load(input_stream)
        self.data = datafile.data
        return self

    def save(self, filename):
        datafile = SequencesDatafile()
        datafile.data = self.data
        datafile.save(filename)
