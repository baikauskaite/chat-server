import socket
import select
from client_message import *
from server_message import *
import signal
import threading


class Controller:

    BUFFER_SIZE = 2048
    MAX_CLIENTS = 66

    def __init__(self, server_address):
        self.__initialize_socket(server_address)
        # Clients' socket list
        self.sockets_list = [self.server_socket]
        # Dictionary of clients: key - socket, value - username
        self.clients = {}
        # self.quit_program is run when program is ended
        signal.signal(signal.SIGINT, self.quit_program)
        self.lock = threading.Lock()
        self.notify_select = open("t.txt", "w")

    # Initialize the server's socket
    def __initialize_socket(self, server_address) -> None:
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allow us to reconnect
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(server_address)
        # Accept only self.MAX_CLIENTS connections
        self.server_socket.listen(self.MAX_CLIENTS)

    # Run the whole server logic
    def run_server(self) -> None:
        while True:
            # read_sockets - sockets on which we have received some kind of data
            # _ - not handled here, should be sockets that are ready to be written to (for ex., checks if the buffers
            # are not full)
            # exception_sockets - sockets with some exception
            read_sockets, _, exception_sockets = select.select(self.sockets_list, [self.notify_select], self.sockets_list)

            for notified_socket in read_sockets:
                # If the socket in which we received data is the server socket, then there's an incoming new connection
                if notified_socket == self.server_socket:
                    client_socket, client_address = self.server_socket.accept()
                    print(client_socket)
                    t = threading.Thread(target=self.helper, args=(client_socket,))
                    t.start()
                # If the socket in which we received data is not the server socket, then it is a client that
                # is already connected
                else:
                    byte_str = self.receive_client_message(notified_socket)

                    # If client message is empty, the client disconnected
                    if not byte_str:
                        print("Closed connection from " + self.clients[notified_socket])
                        self.remove_client(notified_socket)
                        continue

                    client_message = ClientMessage(byte_str, notified_socket)
                    self.match_heading(client_message)

            # Remove any sockets that had exceptions from clients' list
            for notified_socket in exception_sockets:
                self.remove_client(notified_socket)

    def helper(self, client_socket):
        client_socket.settimeout(10)
        byte_str = self.receive_client_message(client_socket)

        # If the received message is empty, the client disconnected before sending his name
        if not byte_str:
            return

        client_message = ClientMessage(byte_str, client_socket)
        # Accept only first-handshakes, disconnect if other kind of message
        if client_message.head != "HELLO-FROM":
            client_socket.close()
        else:
            self.hello_from(client_message)

    # Receive message in bytes from client, return empty byte string if there's no message or exception happens
    def receive_client_message(self, client_socket) -> bytes:
        try:
            byte_str = self.receive_client_message_helper(client_socket)
            return byte_str
        except Exception as e:
            print(e)
            return b''

    # Receive client message, ensure the whole message is received no matter the self.BUFFER_SIZE
    def receive_client_message_helper(self, client_socket) -> bytes:
        byte_str = b''
        while True:
            part = client_socket.recv(self.BUFFER_SIZE)

            if not part:
                return b''
            byte_str += part
            decoded_part = part.decode()

            if '\n' in decoded_part:
                return byte_str

    # Match the request's heading and perform a function accordingly
    def match_heading(self, client_message) -> None:
        heading = client_message.head

        # Check whether there exists such a heading, if not, "BAD-RQST-HDR" is sent
        if heading not in self.headings.keys():
            server_message = ServerMessage(client_message.client_socket)
            server_message.bad_rqst_hdr()
            return

        self.headings[heading](self, client_message)

    # Send a "BAD-RQST-BODY" if the body of the request is empty
    def is_empty_body(self, client_socket, body) -> bool:
        if not body:
            server_message = ServerMessage(client_socket)
            server_message.bad_rqst_body()
            return True
        return False

    # Process "HELLO-FROM" request from client
    def hello_from(self, client_message) -> None:
        client_socket = client_message.client_socket

        # Check if there's a username in the request body
        if self.is_empty_body(client_socket, client_message.body):
            return

        username = " ".join(client_message.body)
        server_message = ServerMessage(client_socket)

        self.lock.acquire()
        # Check whether the username is already in use
        if username in self.clients.values():
            server_message.in_use()
        # Check whether number of clients is already self.MAX_CLIENTS
        elif len(self.clients) == self.MAX_CLIENTS:
            server_message.busy()
        # Send second_handshake and append client's socket and username to the clients' list
        else:
            server_message.second_handshake(username)
            self.sockets_list.append(client_socket)
            self.clients[client_socket] = username
            self.notify_select.write(" ")
        self.lock.release()

    # Process "WHO" request from client
    def who(self, client_message) -> None:
        client_socket = client_message.client_socket
        server_message = ServerMessage(client_socket)

        # There should be no body in "WHO" request
        if client_message.body:
            server_message.bad_rqst_body()
            return

        usernames = self.clients.values()
        server_message.who_ok(usernames)

    # Process "SEND" request from client
    def send(self, client_message) -> None:
        sender_socket = client_message.client_socket
        server_message_to_sender = ServerMessage(sender_socket)
        sender_username = self.clients[sender_socket]
        receiver_socket = None
        is_user_online = False

        # Check if the request body is not empty
        if self.is_empty_body(sender_socket, client_message.body):
            return
        receiver_username = client_message.body.pop(0)
        # After popping the username from the request body, check if the rest of the body is not empty
        if self.is_empty_body(sender_socket, client_message.body):
            return

        # Search if the user is online and get its socket
        for sock, username in self.clients.items():
            if username == receiver_username:
                receiver_socket = sock
                is_user_online = True
                break

        # Deliver the message to recipient, if it is online, and send "UNKNOWN", if not
        if is_user_online:
            server_message_to_receiver = ServerMessage(receiver_socket)
            server_message_to_receiver.delivery(sender_username, client_message.body)
            server_message_to_sender.send_ok()
        else:
            server_message_to_sender.unknown()

    # Pairs of headings and functions to process the body for the matching heading
    headings = {
        "WHO": who,
        "SEND": send
    }

    # Remove client both from sockets_list and clients' dictionary
    def remove_client(self, client_socket) -> None:
        self.sockets_list.remove(client_socket)
        del self.clients[client_socket]

    # Close the server_socket before the end of the program
    def quit_program(self, signum, frame) -> None:
        self.server_socket.close()
        self.notify_select.close()
        exit()
