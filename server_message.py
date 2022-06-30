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
        self.__send_message_to_client(f"HELLO {username}")

    def send_ok(self) -> None:
        self.__send_message_to_client("SEND-OK")
        print("SEND-OK")

    def unknown(self) -> None:
        self.__send_message_to_client("UNKNOWN")
        print("UNKNOWN")

    def delivery(self, username, message) -> None:
        message = " ".join(message)
        self.__send_message_to_client(f"DELIVERY {username} {message}")
        print(f"DELIVERY {username} {message}")

    def in_use(self) -> None:
        self.__send_message_to_client("IN-USE")
        print("IN-USE")

    def busy(self) -> None:
        self.__send_message_to_client("BUSY")
        print("BUSY")

    def who_ok(self, usernames) -> None:
        usernames = ",".join(usernames)
        self.__send_message_to_client("WHO-OK " + usernames)
        print("WHO-OK " + usernames)

    def bad_rqst_hdr(self) -> None:
        self.__send_message_to_client("BAD-RQST-HDR")
        print("BAD-RQST-HDR")

    def bad_rqst_body(self) -> None:
        self.__send_message_to_client("BAD-RQST-BODY")
        print("BAD-RQST-BODY")
