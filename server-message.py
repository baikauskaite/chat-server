class ServerMessage:

    def __init__(self, socket):
        self.socket = socket

    # Private helper for sending messages
    def __send_message_to_client(self, text) -> None:
        message = text + "\n"
        message_bytes = message.encode()
        self.socket.sendall(message_bytes)

    # Responds to the first handshake of the user
    def second_handshake(self, username) -> None:
        self.__send_message_to_client("HELLO " + username)

    def send_ok(self) -> int:
        pass

    def unknown(self) -> int:
        pass

    def delivery(self) -> int:
        pass

    def in_use(self) -> int:
        pass

    def busy(self) -> int:
        pass

    def who_ok(self) -> int:
        pass

    def bad_rqst_hdr(self) -> int:
        pass

    def bad_rqst_body(self) -> int:
        pass
