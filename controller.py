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
        # Dictionary of clients, key - socket, value - username
        self.clients = {}

    def __initialize_socket(self, server_address) -> None:
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allows us to reconnect
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(server_address)
        self.server_socket.listen()

    def receive_client_message(self, client_socket):
        try:
            byte_str = client_socket.recv(self.BUFFER_SIZE)
            message = byte_str.decode()
            # Temporary solution
            if "\n" not in message:
                return False
            return byte_str
        except Exception as e:
            print(e)
            return False

    def match_heading(self, client_message):
        self.headings[client_message.head](self, client_message)

    def hello_from(self, client_message):
        client_socket = client_message.client_socket
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
        usernames = self.clients.values()
        server_message.who_ok(usernames)

    def send(self, client_message):
        sender_socket = client_message.client_socket
        server_message_to_sender = ServerMessage(sender_socket)
        sender_username = self.clients[sender_socket]
        receiver_username = client_message.body.pop(0)

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
                        self.sockets_list.remove(notified_socket)
                        del self.clients[notified_socket]
                        continue

                    client_message = ClientMessage(byte_str, notified_socket)
                    self.match_heading(client_message)

            for notified_socket in exception_sockets:
                self.sockets_list.remove(notified_socket)
                del self.clients[notified_socket]
