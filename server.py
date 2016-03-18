from twisted.protocols import basic
from twisted.internet import protocol
from twisted.application import service, internet
from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor, defer

from lib.room import Room
from lib.player import Player

import logging
import argparse
import traceback
import random
import itertools



logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d %I:%M:%S %p', level=logging.DEBUG)


parser = argparse.ArgumentParser(description='Pentago server.')
parser.add_argument("port", type=int, help="Port on which to listen for connections")
parser.add_argument("player_count", type=int, help="Number of players")
parser.add_argument("--move_time", "-t", type=int, default=60, help="Time per move in seconds")
parser.add_argument("--iterations", "-i", type=int, default=1, help="Play through this many permutations of player play order before stopping")


args = parser.parse_args()


class Manager(object):
    def __init__(self):
        self.rooms = {}

    def room_for_id(self, room_id):
        if not room_id in self.rooms:
            logging.info("Creating room with room_id %s" % room_id)
            self.rooms[room_id] = Room(room_id, args.player_count, args.move_time, args.iterations) 
        return self.rooms[room_id]
    
    def add_player_to_room(self, player, room):
        room.add_player(player) 
                     
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
                if self.player:
                    self.player.send_message(["INFO", e.message])

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