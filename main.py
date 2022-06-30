from controller import *
import os

HOST_NAME = os.environ['HOST']
PORT_NUMBER = int(os.environ['PORT'])
server_address = (HOST_NAME, PORT_NUMBER)

controller = Controller(server_address)
# Run the whole server logic
controller.run_server()
