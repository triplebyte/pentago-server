import unittest
import math
import copy
import pentago_board

class TestGroupExtractor(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_ranges(self):
        game = pentago_board.PentagoBoard(3, 3, 5)
        assert not game.make_move(-1, 0, 1, 0, 0, 'r')
        assert not game.make_move(0, 0, 1, 30, 0, 'r')
        assert not game.make_move(0, 0, 1, 0, 0, 'p')
        assert game.make_move(0, 0, 1, 2, 2, 'l')
        assert not game.make_move(0, 0, 1, 2, 2, 'l')


        for i in range(81):
            game.board[i / 9][i % 9] = i
        
        game2 = copy.deepcopy(game)
        game.do_rotation(2, 0, 'r')
        
        game2.do_rotation(2, 0, 'l')
        game2.do_rotation(2, 0, 'l')
        game2.do_rotation(2, 0, 'l')

        assert game2.board == game.board

    def test_win(self):
        game = pentago_board.PentagoBoard(3, 3, 5)
        assert game.get_winners() == set()
        game.board[0][0] = 1
        game.board[0][1] = 1
        game.board[0][2] = 1
        game.board[0][3] = 1
        assert game.get_winners() == set()
        game.board[0][4] = 1
        assert game.get_winners() == set([1])
        
        game.board[5][6] = 2
        game.board[6][6] = 2
        game.board[7][6] = 2
        game.board[8][6] = 2
        
        assert game.get_winners() == set([1])
        game.board[4][6] = 2
        assert game.get_winners() == set([1, 2])

        game.board[0][8] = 3
        game.board[1][7] = 3
        game.board[2][6] = 3
        game.board[3][5] = 3
        assert game.get_winners() == set([1, 2])
        game.board[4][4] = 3       
        assert game.get_winners() == set([1, 2, 3])
        
        game.board[1][0] = 4
        game.board[2][1] = 4
        game.board[3][2] = 4
        game.board[4][3] = 4
        assert game.get_winners() == set([1, 2, 3])
        game.board[5][4] = 4
        assert game.get_winners() == set([1, 2, 3, 4])

