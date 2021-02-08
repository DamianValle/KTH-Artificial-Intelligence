from player_utils import PlayerController


class PlayerControllerHMMAbstract(PlayerController):
    def __init__(self):
        super().__init__()
        self.__name2id = dict()

    def player_loop(self):
        """
        Function that generates the loop of the game. In each iteration
        the agent calculates the best next movement and send this to the game
        through the sender. Then it receives an update of the game through
        receiver, with this it computes the next movement.
        :return:
        """
        self.init_parameters()

        count = 0
        n_fish = 0
        while True:
            msg = self.receiver()
            count += 1

            if count == 1:
                # Initialize name2id map
                for key in msg.keys():
                    if key.startswith('fish'):
                        if key not in self.__name2id:
                            id = len(self.__name2id)
                            self.__name2id[key] = id

                n_fish = len(self.__name2id)

            observations = [0] * n_fish
            for key in msg.keys():
                if key in self.__name2id:
                    observations[self.__name2id[key]] = msg[key]

            guess_result = self.guess(count, observations)
            if guess_result is None:
                msg = {'guessing': False}
                self.sender(msg)
            elif type(guess_result) is tuple:
                fish_id, fish_type = guess_result
                msg = {'guessing': True, 'id': fish_id, 'type': fish_type}
                self.sender(msg)
                msg2 = self.receiver()
                self.reveal(msg2['correct'], msg2['id'], msg2['type'])
            else:
                raise Exception(f'Wrong return type: {type(guess_result)}')

    def init_parameters(self):
        raise NotImplementedError()

    def guess(self, step, observations):
        raise NotImplementedError()

    def reveal(self, correct, fish_id, true_type):
        raise NotImplementedError()
