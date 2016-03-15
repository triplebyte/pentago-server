import logging
import socket 

class BaseClient(object):
	def __init__(self, host, port, name, game_id):
		self.host = host 
		self.port = port
		self.name = name
		self.game_id = game_id
		self.socket = None

	def connect(self):
		logging.info("Connecting to %s:%s" % (self.host, self.port))
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.connect((self.host, self.port))
		logging.debug("sending join")
		self.send_message(['JOIN', self.name, self.game_id])
		logging.debug("Sent!")

	def wait_for_messages(self): 
		lines = []
		for line in self.socket.makefile():
			if len(line.strip()) == 0:
				if len(lines):
					self.handle_message(lines[0].upper(), lines[1:])
				lines = []
			else:
				lines.append(line.strip())

	def send_message(self, message): 
		self.socket.send('\n'.join(message) + '\n\n')

	def handle_message(self, action, message):
		pass 
