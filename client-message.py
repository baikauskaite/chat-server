class ClientMessage:

    # Splitting the message into a heading and a body
    def __init__(self, byte_str):
        self.head = None
        self.body = None
        # TODO: process client message
        self.code = self.process_client_message(byte_str)

    # Split client message to head and body
    def split_message(self, message):
        message = message.rstrip()
        word_list = message.split()
        self.head = word_list.pop(0)
        self.body = word_list

    # Decode and split the client message from the client and determine what kind of message it is
    def process_client_message(self, byte_str) -> int:
        decoded_str = byte_str.decode()
        self.split_message(decoded_str)
        code = self.match_heading()
        return code

    # Pairs of headings and functions to process the body for the matching heading
    headings = {
        "HELLO-FROM": lambda x: print("This is not implemented."),
    }

    def match_heading(self) -> int:
        return self.headings[self.head](self)
