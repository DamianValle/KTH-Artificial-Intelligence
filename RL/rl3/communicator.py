import sys


class Communicator:
    """
    Communicator allows two classes in different processes to communicator with each other
    """
    def __init__(self):
        self.receiver_pipe = None
        self.sender_pipe = None

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
        msg = self.receiver_pipe.recv()
        self.check_game_over(msg)
        return msg

    def check_game_over(self, msg):
        """
        Check if game is over and if it is, close process
        :param msg:
        :return:
        """
        if msg.get("game_over"):
            print("Game over!")
            sys.exit(0)

    def sender(self, msg):
        """
        Send message to the sender pipe
        :param msg:
        :return:
        """
        self.sender_pipe.send(msg)
