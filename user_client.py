import logging
import argparse
import pentago_board
import random
import os

import base_client 
parser = argparse.ArgumentParser(description='User pentago client.')
parser.add_argument("host", type=str, help="Host of pentago server")
parser.add_argument("port", type=int, help="Port of pentago server")
parser.add_argument("name", type=str, help="Player name")
parser.add_argument("room_id", type=str, help="room_id to join")

args = parser.parse_args()

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d %I:%M:%S %p', level=logging.DEBUG)


class UserClient(base_client.BaseClient):
	def __init__(self, host, port, name, room_id):
		super(UserClient, self).__init__(host, port, name, room_id)

	def handle_message(self, action, message):
		print "Received %s %s" % (action, message)
		if action == "GAME_STARTED":
			print "Game started"
			for l in message:
				i, name = l.split(' ', 1)
				if name == self.name:
					print "We are player number %s" % i

		elif action == "MAKE_MOVE":
			self.make_move(message)
		elif action == "BAD_MOVE":
			print "Bad move!"
			self.get_move()
		elif action == "PLAYER_MOVED":
			self.player_moved(message)
		elif action == "GAME_OVER":
			print "Game is over! Winners: %s" % (message)

		elif action == "GAME_DRAW":
			print "Game is a draw!"


	def player_moved(self, message):
		os.system('clear')
		board = pentago_board.PentagoBoard(3, 3, 5)
		board.set_from_array([int (c) for c  in message[1].split(' ')])
		print board

	def get_point(self, dim, text):
		x,y = -1,-1
		while not (0 <= x < dim and 0 <= y < dim):
			try:
				rx, ry = raw_input(text).split(',')
				x = int(rx)
				y = int(ry)
			except ValueError:
				pass
		return x, y

	def make_move(self, message):
		board = pentago_board.PentagoBoard(3, 3, 5)
		board.set_from_array([int (c) for c  in message[1].split(' ')])
		duration = int(message[0])
		os.system('clear')
		print board
		print "Make a move (you have %s seconds)" % (duration)
		self.get_move()

	def get_move(self):
		px, py = self.get_point(9, "Where do you want to drop a stone? (x, y): ")
		rx, ry = self.get_point(3, "Where do you want to rotate? (x, y):")
		r = None
		while not r in ['l', 'r']:
			r = raw_input("What direction do you to rotate? (l or r): ")  
		self.send_message(["PLAY" , "%s %s %s %s %s" % (px, py, rx, ry, r)])


client = UserClient(args.host, args.port, args.name, args.room_id)
client.connect()
client.wait_for_messages()
