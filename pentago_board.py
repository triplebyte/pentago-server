import logging 
import copy 

class PentagoBoard(object):
	def __init__(self, block_width, block_count, winning_length):
		self.block_width = block_width
		self.block_count = block_count
		self.winning_length = winning_length
		dim = block_width * block_count
		self.board = [[0]*dim for _ in range(dim)]

	def set_from_array(self, array):
		dim = self.block_width * self.block_count
		for i, v in enumerate(array):
			self.board[i / dim][i % dim] = v

	def get_winners(self):
		winners = set()
		for y in range(len(self.board)):
			for x in range(len(self.board[0])):
				w = self.get_winner_at_loc(x, y)
				if w:
					winners.add(w)
		return winners

	def in_range(self, x, y):
		return y >= 0 and y < len(self.board) and x >= 0 and x < len(self.board[0])  

	def get_winner_at_loc(self, x, y):
		if not self.board[y][x]:
			return None
		for xd, yd in [(1, 0), (0, 1), (1, 1), (1, -1)]:
			for i in range(1, self.winning_length):
				xp = x + i*xd
				yp = y + i*yd
				if not self.in_range(xp, yp) or self.board[yp][xp] != self.board[y][x]:
					break
			else: # Boom! Use of python else on for loop! 
				return self.board[y][x]
		return None
	
	def block_in_range(self, x, y):
		return x >= 0 and x < self.block_width and y >= 0 and y < self.block_width


	def make_move(self, piece_x, piece_y, player, block_x, block_y, rotation):
		""" Make a move on the board. block_x/y are the coordinates of the block to rotate. piece_x/y are the piece to place""" 
		if not self.block_in_range(block_x, block_y):
			logging.warn("Bad block coordinate: (%s, %s)" % (block_x, block_y))
			return False

		if not self.in_range(piece_x, piece_y):
			logging.warn("Bad piece coordinate: (%s, %s)" % (piece_x, piece_y))
			return False
		
		if self.board[piece_y][piece_x]: 
			logging.warn("Trying to place in non-empty spot: (%s, %s)" % (piece_x, piece_y))
			return False
		
		if not rotation in ['r', 'l']:
			logging.warn("Bad rotation value: %s" % (rotation,))
			return False

		self.board[piece_y][piece_x] = player 
		self.do_rotation(block_x, block_y, rotation)
		return True 
	
	def do_rotation(self, block_x, block_y, rotation):
		board = copy.deepcopy(self.board)
		for y in range(self.block_width):
			for x in range(self.block_width):
				ox = self.block_width * block_x
				oy = self.block_width * block_y
	
				if rotation == 'r':
					dx = y
					dy = (self.block_width - 1 - x)
				else:
					dx = (self.block_width - 1 - y)
					dy = x
				self.board[oy + y][ox + x] = board[oy + dy][ox + dx]
	
	def is_full(self):
		return not any([0 in l for l in self.board]) 

	def __str__(self):
		return '\n'.join([', '.join([str(c) for c in l]) for l in self.board])

	def network_format(self):
		return ' '.join([' '.join([str(c) for c in l]) for l in self.board])




