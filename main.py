from controller import *

HOST_NAME = socket.gethostname()
PORT_NUMBER = 1234
server_address = (HOST_NAME, PORT_NUMBER)

controller = Controller(server_address)
controller.run_server()
