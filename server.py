from twisted.protocols import basic
from twisted.internet import protocol
from twisted.application import service, internet
from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor, defer

import logging
import argparse
import traceback
import random

import pentago_board

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d %I:%M:%S %p', level=logging.DEBUG)


parser = argparse.ArgumentParser(description='Pentago server.')
parser.add_argument("port", type=int, help="Port on which to listen for connections")
parser.add_argument("player_count", type=int, help="Number of players")
parser.add_argument("move_time", type=int, help="Time per move in seconds")

args = parser.parse_args()


class Player(object):
    def __init__(self, name, connection):
        self.name = name 
        self.connection = connection
    
    def send_message(self, message):
        self.connection.transport.write('\n'.join(message) + '\n\n')


class Game(object):
    def __init__(self, game_id, player_count):
        self.game_id = game_id 
        self.player_count = player_count
        self.players = []
        self.active_player = None

    def add_player(self, player):
        assert len(self.players) <  self.player_count 
        assert not player.name in [p.name for p in self.players], "Name is not unique"
        self.players.append(player)
        logging.info("Player %s joined game %s (%d out of %d)" % (player.name, self.game_id, len(self.players), self.player_count))

    def remove_player(self, player):
        if player in self.players: 
            i = self.players.index(player)
            self.players.remove(player)

            #We removed the current active player. Move back, so on next timeout the correct next player will play  
            if self.active_player == player and len(self.players) > 0:
                self.active_player = self.players[i - 1]

             
    def start_game(self):
        logging.info("Game %s starting" % (self.game_id))
        
        self.board = pentago_board.PentagoBoard(3, 3, 5)

        random.shuffle(self.players)
        for i in range(len(self.players)):
            self.players[i].piece = i + 1

        self.send_message_to_players(['GAME_STARTED'] + ["%d %s" % (p.piece, p.name) for p in self.players])
        self.active_player = self.players[0]
        self.do_active_player_turn()

    def do_active_player_turn(self):
        self.player_timeout = reactor.callLater(args.move_time + 1.0, self.player_turn_timeout) 
        self.active_player.send_message(['MAKE_MOVE', str(args.move_time), self.board.network_format()])

    def player_turn_timeout(self):
        logging.info("Player %s timed out" % (self.active_player.name))
        self.send_message_to_players(['INFO', "Player %s timed out" % self.active_player.name])
        self.advance_player()

    def advance_player(self):
        if self.active_player in self.players:
            i = self.players.index(self.active_player)
            i = (i + 1) % len(self.players)
            self.active_player = self.players[i]
            self.do_active_player_turn()


    def send_message_to_players(self, message):
        for p in self.players:
            p.send_message(message) 
    
    def handle_play_message(self, message, player):
        assert len(message) == 1
        px, py, rx, ry, r = message[0].split(" ")
        if self.board.make_move(int(px), int(py), player.piece, int(rx), int(ry), r):
            self.player_timeout.cancel()
            winners = self.board.get_winners()
            if len(winners):
                self.send_message_to_players(['GAME_OVER'] + [self.players[p-1].name for p in winners])       
                
                #and start a new one!
                self.start_game()
            elif self.board.is_full():
                self.send_message_to_players(['GAME_DRAW'])

                self.start_game()
            else:
                self.advance_player()

        else:
            player.send_message(["BAD_MOVE"])


    def message_recieved(self, action, message, player):
        if player == self.active_player:
            if action == "PLAY":
                self.handle_play_message(message, player)   

class Manager(object):
    def __init__(self):
        self.games = {}

    def game_for_id(self, game_id):
        if not game_id in self.games:
            logging.info("Creating game with game_id %s" % game_id)
            self.games[game_id] = Game(game_id, args.player_count) 
        return self.games[game_id]
    
    def add_player_to_game(self, player, game):
        game.add_player(player)
        if len(game.players) == game.player_count:
            game.start_game()

    def remove_player_from_game(self, player, game): 
        game.remove_player(player)
        if len(game.players) == 0:
            logging.info("Deleting game %s" %game.game_id)
            del self.games[game.game_id]
        
manager = Manager()

class PentagoServer(basic.LineReceiver):
    
    delimiter = '\n'

    def connectionMade(self):
        print "Client joined: %s" % (self,)
        self.factory.clients.append(self)
        self.lines = []
        self.game = None
        self.player = None
    
    def connectionLost(self, reason):
        print "Client left: %s" % (self,)    
        self.factory.clients.remove(self)
        if self.game and self.player:
            manager.remove_player_from_game(self.player, self.game) 

    def lineReceived(self, line):
        #end of message 
        if len(line.strip()) == 0:
            try:
                self.message_recieved(self.lines[0].upper(), self.lines[1:])
                self.lines = []
            except Exception, e:
                traceback.print_exc()
                self.transport.loseConnection()  
        else:
            self.lines.append(line)

    def message_recieved(self, action, message):
        logging.debug("message_recieved %s %s" % (action, message))  
        if not self.player or not self.game :
            assert action == "JOIN" and len(message) == 2, "Bad join message"
            player_name = message[0]
            game_id = message[1]
            self.player = Player(player_name, self)
            self.game = manager.game_for_id(game_id)
            manager.add_player_to_game(self.player, self.game)
        else: 
            self.game.message_recieved(action, message, self.player) 





logging.info("Starting server on port %s" % (args.port,))

factory = Factory()
factory.protocol = PentagoServer
factory.clients = []
reactor.listenTCP(args.port, factory)
reactor.run()