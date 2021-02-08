import sys


class Communicator:
    """
    Communicator allows two classes in different processes to communicator with each other
    """

    def __init__(self, receiver_threshold=None):
        self.receiver_pipe = None
        self.sender_pipe = None
        self.receiver_threshold = receiver_threshold

    def set_receive_send_pipes(self, recv_pipe, sender_pipe):
        """
        Set the pipes
        :param recv_pipe: Receiver pipe
        :param sender_pipe: Sender pipe
        :return:
        """
        self.receiver_pipe = recv_pipe
        self.sender_pipe = sender_pipe

    def receiver(self):
        """
        Receive message from the receiver pipe
        :return:
        """
        if not self.receiver_pipe.poll(self.receiver_threshold):
            sys.exit(-1)  # time limit
        msg = self.receiver_pipe.recv()
        self.check_game_over(msg)
        return msg

    @staticmethod
    def check_game_over(msg):
        """
        Check if game is over and if it is, close process
        :param msg:
        :return:
        """
        if msg.get("game_over"):
            sys.exit(0)

    def sender(self, msg):
        """
        Send message to the sender pipe
        :param msg:
        :return:
        """
        self.sender_pipe.send(msg)
