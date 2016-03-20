import logging
import argparse
import lib.pentago_board
import random
import os
import subprocess
import time
import lib.base_client
import socket
parser = argparse.ArgumentParser(description='Wrapper pentago client.')
parser.add_argument("host", type=str, help="Host of pentago server")
parser.add_argument("port", type=int, help="Port of pentago server")
parser.add_argument("name", type=str, help="Player name")
parser.add_argument("room_id", type=str, help="room to join")
parser.add_argument("command", type=str, help="Command to run to get a move")

args = parser.parse_args()

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d %I:%M:%S %p', level=logging.DEBUG)


class WrapperClient(lib.base_client.BaseClient):
	def __init__(self, host, port, name, room_id):
		super(WrapperClient, self).__init__(host, port, name, room_id)

	def handle_message(self, action, message):
		print "Got message %s %s" % (action, message)
		if action == "MAKE_MOVE":
			self.make_move(message)
		elif action == "BAD_MOVE":
			print "Bad move!"
			self.make_move(message)

	def make_move(self, message):
		duration = int(message[0])
		board = message[1]
		proc = subprocess.Popen("%s %s" % (args.command, duration), shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
		move = proc.communicate(board+"\n")[0].strip()
		print "Got move",  move
		self.send_message(["PLAY" , move])

while True:
	try:
		client = WrapperClient(args.host, args.port, args.name, args.room_id)
		client.connect()
		client.wait_for_messages()
	except socket.error, e:
		print e
	print "Disconnected"
	time.sleep(5)
	print "Reconnecting"


