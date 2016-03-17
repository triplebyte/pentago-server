from twisted.protocols import basic
from twisted.internet import protocol
from twisted.application import service, internet
from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor, defer

import logging
import argparse
import traceback
import random
import itertools

import pentago_board

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d %I:%M:%S %p', level=logging.DEBUG)


parser = argparse.ArgumentParser(description='Pentago server.')
parser.add_argument("port", type=int, help="Port on which to listen for connections")
parser.add_argument("player_count", type=int, help="Number of players")
parser.add_argument("--move_time", "-t", type=int, default=60, help="Time per move in seconds")
parser.add_argument("--iterations", "-i", type=int, default=1, help="Play through this many permutations of player play order before stopping")


args = parser.parse_args()


class Player(object):
    def __init__(self, name, connection):
        self.name = name 
        self.connection = connection
    
    def send_message(self, message):
        self.connection.transport.write('\n'.join(message) + '\n\n')

class Room(object):
    def __init__(self, room_id, player_count):
        self.room_id = room_id 
        self.player_count = player_count
        self.players = []
        self.active_player = None
        self.permutations = None
        self.games_played = 0

    def add_player(self, player):
        assert len(self.players) <  self.player_count 
        assert not player.name in [p.name for p in self.players], "Name is not unique"
        self.players.append(player)
        logging.info("Player %s joined room %s (%d out of %d)" % (player.name, self.room_id, len(self.players), self.player_count))

    def remove_player(self, player):
        if player in self.players: 
            i = self.players.index(player)
            self.players.remove(player)

            #We removed the current active player. Move back, so on next timeout the correct next player will play  
            if self.active_player == player and len(self.players) > 0:
                self.active_player = self.players[i - 1]
    # def start_games(self):
    #     self.permutations = itertools.permutations
    #     self.start_next_game()       
             
    def start_game(self):
        logging.info("Game %s starting" % (self.room_id))
        
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
            self.send_message_to_players(['PLAYER_MOVED', self.active_player.name, self.board.network_format()])

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
            player.send_message(["BAD_MOVE", str(args.move_time), self.board.network_format()])


    def message_recieved(self, action, message, player):
        if player == self.active_player:
            if action == "PLAY":
                self.handle_play_message(message, player)   

class Manager(object):
    def __init__(self):
        self.rooms = {}

    def room_for_id(self, room_id):
        if not room_id in self.rooms:
            logging.info("Creating room with room_id %s" % room_id)
            self.rooms[room_id] = Room(room_id, args.player_count) 
        return self.rooms[room_id]
    
    def add_player_to_room(self, player, room):
        room.add_player(player)
        if len(room.players) == room.player_count:
            room.start_game()

    def remove_player_from_room(self, player, room): 
        room.remove_player(player)
        if len(room.players) == 0:
            logging.info("Deleting room %s" %room.room_id)
            del self.rooms[room.room_id]
        
manager = Manager()

class PentagoServer(basic.LineReceiver):
    
    delimiter = '\n'

    def connectionMade(self):
        print "Client joined: %s" % (self,)
        self.factory.clients.append(self)
        self.lines = []
        self.room = None
        self.player = None
    
    def connectionLost(self, reason):
        print "Client left: %s" % (self,)    
        self.factory.clients.remove(self)
        if self.room and self.player:
            manager.remove_player_from_room(self.player, self.room) 

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
        if not self.player or not self.room :
            assert action == "JOIN" and len(message) == 2, "Bad join message"
            player_name = message[0]
            room_id = message[1]
            self.player = Player(player_name, self)
            self.room = manager.room_for_id(room_id)
            manager.add_player_to_room(self.player, self.room)
        else: 
            self.room.message_recieved(action, message, self.player) 





logging.info("Starting server on port %s" % (args.port,))

factory = Factory()
factory.protocol = PentagoServer
factory.clients = []
reactor.listenTCP(args.port, factory)
reactor.run()