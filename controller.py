import socket
import select
from client_message import *
from server_message import *


class Controller:

    BUFFER_SIZE = 2048
    MAX_CLIENTS = 64

    def __init__(self, server_address):
        self.__initialize_socket(server_address)
        # Clients' socket list
        self.sockets_list = [self.server_socket]
        # Dictionary of clients: key - socket, value - username
        self.clients = {}

    def __initialize_socket(self, server_address) -> None:
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allows us to reconnect
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(server_address)
        self.server_socket.listen(self.MAX_CLIENTS)

    def receive_client_message(self, client_socket):
        try:
            byte_str = self.receive_client_message_helper(client_socket)
            if byte_str == b'':
                return False
            return byte_str
        except Exception as e:
            print(e)
            return False

    def receive_client_message_helper(self, client_socket) -> bytes:
        byte_str = b''
        while True:
            part = client_socket.recv(self.BUFFER_SIZE)
            if not part:
                return b''
            byte_str += part
            message = part.decode()
            if '\n' in message:
                return byte_str

    # Matches the request's heading and performs a function accordingly
    def match_heading(self, client_message):
        heading = client_message.head

        # Checks whether there exists such a heading, if not, "BAD-RQST-HDR" is sent
        if heading not in self.headings.keys():
            server_message = ServerMessage(client_message.client_socket)
            server_message.bad_rqst_hdr()
            return

        self.headings[heading](self, client_message)

    # Sends a "BAD-RQST-BODY" if the body of the request is empty
    def is_empty_body(self, client_socket, body) -> bool:
        if not body:
            server_message = ServerMessage(client_socket)
            server_message.bad_rqst_body()
            return True
        return False

    def hello_from(self, client_message):
        client_socket = client_message.client_socket

        # Check if there's a username in the request body
        if self.is_empty_body(client_socket, client_message.body):
            return

        username = " ".join(client_message.body)
        server_message = ServerMessage(client_socket)

        if username in self.clients.values():
            server_message.in_use()
        elif len(self.clients) == self.MAX_CLIENTS:
            server_message.busy()
        else:
            server_message.second_handshake(username)
            self.sockets_list.append(client_socket)
            self.clients[client_socket] = username

    def who(self, client_message):
        client_socket = client_message.client_socket
        server_message = ServerMessage(client_socket)

        # There should be no body in "WHO" request
        if client_message.body:
            server_message.bad_rqst_body()
            return

        usernames = self.clients.values()
        server_message.who_ok(usernames)

    def send(self, client_message):
        sender_socket = client_message.client_socket
        server_message_to_sender = ServerMessage(sender_socket)
        sender_username = self.clients[sender_socket]

        # Check if the request body is not empty
        if self.is_empty_body(sender_socket, client_message.body):
            return

        receiver_username = client_message.body.pop(0)

        # After popping the username from the request body, check if the rest of the body is not empty
        if self.is_empty_body(sender_socket, client_message.body):
            return

        receiver_socket = None
        is_user_online = False

        for sock, username in self.clients.items():
            if username == receiver_username:
                receiver_socket = sock
                is_user_online = True
                break

        if is_user_online:
            server_message_to_receiver = ServerMessage(receiver_socket)
            server_message_to_receiver.delivery(sender_username, client_message.body)
            server_message_to_sender.send_ok()
        else:
            server_message_to_sender.unknown()

    # Pairs of headings and functions to process the body for the matching heading
    headings = {
        "HELLO-FROM": hello_from,
        "WHO": who,
        "SEND": send
    }

    # Removes client both from sockets_list and clients dictionary
    def remove_client(self, client_socket):
        self.sockets_list.remove(client_socket)
        del self.clients[client_socket]

    def run_server(self):
        while True:
            read_sockets, _, exception_sockets = select.select(self.sockets_list, [], self.sockets_list)

            for notified_socket in read_sockets:
                if notified_socket == self.server_socket:
                    client_socket, client_address = self.server_socket.accept()
                    print(client_socket)

                    byte_str = self.receive_client_message(client_socket)
                    if not byte_str:
                        continue

                    client_message = ClientMessage(byte_str, client_socket)
                    self.match_heading(client_message)

                else:
                    byte_str = self.receive_client_message(notified_socket)

                    if not byte_str:
                        print("Closed connection from " + self.clients[notified_socket])
                        self.remove_client(notified_socket)
                        continue

                    client_message = ClientMessage(byte_str, notified_socket)
                    self.match_heading(client_message)

            for notified_socket in exception_sockets:
                self.remove_client(notified_socket)
