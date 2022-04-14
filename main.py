import socket
import select

HOST_NAME = "127.0.0.1"
PORT_NUMBER = 1234

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((HOST_NAME, PORT_NUMBER))

server_socket.listen()
