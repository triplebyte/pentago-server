import logging
import argparse
import pentago_board
import random

import base_client 
parser = argparse.ArgumentParser(description='Random pentago client.')
parser.add_argument("host", type=str, help="Host of pentago server")
parser.add_argument("port", type=int, help="Port of pentago server")
parser.add_argument("name", type=str, help="Player name")
parser.add_argument("game_id", type=str, help="game_id to join")

args = parser.parse_args()

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d %I:%M:%S %p', level=logging.DEBUG)


class RandomClient(base_client.BaseClient):
	def __init__(self, host, port, name, game_id):
		super(RandomClient, self).__init__(host, port, name, game_id)

	def handle_message(self, action, message):
		print "Received %s %s" % (action, message)
		if action == "MAKE_MOVE":
			self.make_move(message)

	def make_move(self, message):
		board = pentago_board.PentagoBoard(3, 3, 5)
		board.set_from_array([int (c) for c  in message[1].split(' ')])
		moves = [(x, y) for x in range(9) for y in range(9) if board.board[y][x] == 0]
		random.shuffle(moves)
		move = moves[0]
		rotation = (random.choice(range(3)), random.choice(range(3)))
		d = random.choice(['r', 'l'])
		self.send_message(["PLAY" , "%s %s %s %s %s" % (move[0], move[1], rotation[0], rotation[1], d)])



client = RandomClient(args.host, args.port, args.name, args.game_id)
client.connect()
client.wait_for_messages()
