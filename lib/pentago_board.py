import logging
import copy
from termcolor import colored


class PentagoBoard(object):
	def __init__(self, block_width, block_count, winning_length):
		self.block_width = block_width
		self.block_count = block_count
		self.winning_length = winning_length
		dim = block_width * block_count
		self.board = [[0]*dim for _ in range(dim)]
		self.last_play = (-1, -1)
		self.last_rotation = (-1, -1, 'r')
		

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

		
		block_width = self.block_width
		if (piece_x/3, piece_y/3) == (block_x, block_y):
			ox, bx = (piece_x/block_width)*block_width, piece_x%block_width
			oy, by = (piece_y/block_width)*block_width, piece_y%block_width
			if rotation == 'l':
				bx, by = by, block_width - 1 - bx
			else:
				bx, by =  block_width - 1 - by, bx
			piece_x = ox + bx
			piece_y = oy + by

		self.last_play = (piece_x, piece_y)
		self.last_rotation = (block_x, block_y, rotation)



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

	def group_by(self, array, n, separator):
		rtn = array[0:n]
		for i in range(n, len(array), n):
			rtn.append(separator)
			rtn.extend(array[i:i+n])
		return rtn

	def __str__(self):
		colors = {0: 'grey', 1:'red', 2:'green', 3:'yellow', 4:'blue'}
		b = [' '.join(self.group_by([colored(str(c), colors[c]) if c else str(c) for c in l], 3, ' ')) for l in self.board]
		b = self.group_by(b, 3, ' ' * len(b[0]))
		return '\n'.join(b)

	def network_format(self):
		return ' '.join([' '.join([str(c) for c in l]) for l in self.board])

	def render_html(self):
		colors = {0:'black', 1:'red', 2:'green', 3:'blue', 4:'purple'}
		rtn = "<p><div style='position: relative; display: inline-block'><table>"

		rotation_marker = ''
		if self.last_rotation[0] >= 0:
			l = '%s%%' % ((self.last_rotation[0]) * 33.3 + 33.3/2 - 4)
			t = '%s%%' % ((self.last_rotation[1]) * 33.3 - 4)
			rotation_marker = "<div style='position: absolute; left: %s; top: %s'>%s</div>" % (l, t, '&#8594;' if (self.last_rotation[2] == 'r') else '&#8592;')

		for y, row in enumerate(self.board):
			if y > 0 and y % 3 == 0:
				rtn += "<tr>" + "<td></td>" * 9 + "</tr>"
			line = "<tr>"
			for x, cell in enumerate(row):
				if x > 0 and x % 3 == 0:
					line += "<td></td>"

				v = "<b>%s</b>" % (cell,) if self.last_play == (x, y) else cell
				bgcolor = '#F9F9F9' if self.last_rotation[:2] == (x/3, y/3) else '#FFFFFF'
				line += "<td style='width:20px; color:%s; background-color:%s; text-align: center'>%s</td>" % (colors[cell], bgcolor, v)
			line += "</tr>"
			rtn += line
		rtn += "</table>%s</div></p>" % (rotation_marker,)
		return rtn





