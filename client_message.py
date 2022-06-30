class ClientMessage:

    # Splitting the message into a heading and a body
    def __init__(self, byte_str, client_socket):
        self.head = None
        self.body = None
        self.process_client_message(byte_str)
        self.client_socket = client_socket

    # Split client message to head and body
    def split_message(self, message):
        message = message.rstrip()
        word_list = message.split()
        self.head = word_list.pop(0)
        self.body = word_list

    # Decode and split the client message from the client and determine what kind of message it is
    def process_client_message(self, byte_str):
        decoded_str = byte_str.decode()
        self.split_message(decoded_str)
