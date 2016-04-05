from twisted.internet import reactor, defer

import logging
import random
import itertools
import os

import pentago_board
class Game(object):
    def __init__(self, room, move_time, players):
        self.room  = room
        self.players = players
        self.move_time = move_time

        self.board = pentago_board.PentagoBoard(3, 3, 5)

        self.active_player = None
        self.player_timeout = None


    def remove_player(self, player):
        if player in self.players:
            i = self.players.index(player)
            self.players.remove(player)

            #We removed the current active player. Move back, so on next timeout the correct next player will play
            if self.active_player == player and len(self.players) > 0:
                self.active_player = self.players[i - 1]

            self.room.send_message_to_players(["PLAYER_LEFT_GAME", player.name])

    def start_game(self):
        for i in range(len(self.players)):
            self.players[i].piece = i + 1

        self.room.send_message_to_players(['GAME_STARTED'] + ["%d %s" % (p.piece, p.name) for p in self.players])

        self.active_player = self.players[0]
        self.do_active_player_turn()


    def do_active_player_turn(self):
        self.player_timeout = reactor.callLater(self.move_time + 1.0, self.player_turn_timeout)
        self.active_player.send_message(['MAKE_MOVE', str(self.move_time), self.board.network_format()])

    def player_turn_timeout(self):
        logging.info("Player %s timed out" % (self.active_player.name))
        self.room.send_message_to_players(['INFO', "Player %s timed out" % self.active_player.name])
        self.advance_player()

    def advance_player(self):
        if self.active_player in self.players:
            i = self.players.index(self.active_player)
            i = (i + 1) % len(self.players)
            self.active_player = self.players[i]
            self.do_active_player_turn()


    def handle_play_message(self, message, player):
        if player == self.active_player:
            assert len(message) == 1
            px, py, rx, ry, r = [c for c in message[0].strip().split(" ") if len(c)]
            if self.board.make_move(int(px), int(py), player.piece, int(rx), int(ry), r):
                self.player_timeout.cancel()
                self.room.send_message_to_players(['PLAYER_MOVED', self.active_player.name, self.board.network_format()])

                winners = self.board.get_winners()
                if len(winners) or self.board.is_full():
                    self.room.send_message_to_players(['GAME_OVER'] + [self.players[p-1].name for p in winners])
                    self.room.game_over([self.players[i-1].name for i in winners])
                else:
                    self.advance_player()
            else:
                player.send_message(["BAD_MOVE", str(self.move_time), self.board.network_format()])
        else:
             player.send_message(['INFO', "It is not your turn. You can't send messages"])


class Room(object):
    def __init__(self, room_id, player_count, move_time, games_to_play):
        self.room_id = room_id
        self.players = []
        self.move_time = move_time
        self.player_count = player_count

        self.games_played = 0
        self.active_game = None
        self.state = "waiting"

        self.game_log = []

        self.winning_counts = {}

        #set the order of play that we will use
        self.permutations = []
        while len(self.permutations) < games_to_play:
            self.permutations.extend(itertools.permutations(range(player_count)))
        random.shuffle(self.permutations)
        self.permutations = self.permutations[:games_to_play]




    def add_player(self, player):
        assert len(self.players) < self.player_count, "Game is full!"
        assert not player.name in [p.name for p in self.players], "Name is not unique"
        assert not self.active_game, "Player can't join. Game is active."

        self.players.append(player)
        logging.info("Player %s joined room %s (%d out of %d)" % (player.name, self.room_id, len(self.players), self.player_count))

        if len(self.players) == self.player_count :
            self.start_game()


    def remove_player(self, player):
        if player in self.players:
            self.players.remove(player)
        if self.active_game:
            self.active_game.remove_player(player)

    def start_game(self):
        if len(self.permutations) == 0:
            self.state = "finished"
            logging.info("Games over!")
            logging.info("winning_counts: %s" % self.winning_counts)

        else:
            self.state = "active"
            logging.info("Game %s starting (%s of %s)" % (self.room_id, self.games_played, self.games_played + len(self.permutations)))

            #sort so we have a consistent ordering as players join
            self.players.sort(key=lambda p:p.name)
            permutation = self.permutations.pop()
            game_players = [self.players[i] for i in permutation]
            self.active_game = Game(self, self.move_time, game_players)
            self.active_game.start_game()

    def write_log(self):
        d = "games/%s" % self.room_id
        if not os.path.exists(d):
            os.makedirs(d)

        f = open('%s/%s_%s.game' % (d, self.room_id, self.games_played), 'w')
        f.write(''.join(self.game_log))
        f.close()
        self.game_log = []


    def game_over(self, winners):
        logging.info("The game is over! Winners: %s" % winners)
        self.write_log()
        self.games_played += 1

        if len(winners):
            for w in winners:
                self.winning_counts[w] = self.winning_counts.get(w, 0) + 1
        else:
            self.winning_counts["draws"] = self.winning_counts.get("draws", 0) + 1

        reactor.callLater(5.0, self.start_game)

    def message_recieved(self, action, message, player):
        if self.active_game and action == "PLAY":
            self.active_game.handle_play_message(message, player)

    def send_message_to_players(self, message):
        self.game_log.append('\n'.join(message)+'\n\n')
        for p in self.players:
            p.send_message(message)

    def render_players(self):
        rtn = "<p><p><b>Players:</b></p><table>"
        for p in sorted(self.players, key=lambda p:p.piece):
            name = "<b>%s</b>" % (p.name,) if (self.active_game and p == self.active_game.active_player) else p.name
            rtn += "<tr><td>%s</td><td>%s</td></tr>" % (p.piece, name)

        rtn += "</table></p>"
        return rtn
    def render_wins(self):
        rtn = "<p><p><b>Win counts:</b></p><table>"
        for p in self.winning_counts:
            rtn += "<tr><td>%s</td><td>%s</td></tr>" % (self.winning_counts[p], p)
        rtn += "</table></p>"
        return rtn

    def render(self):
        rtn = "<p><b>Game %s (out of %s)</b></p>" % (self.games_played, self.games_played + len(self.permutations))
        rtn += self.render_players()
        if self.active_game:
            rtn += self.active_game.board.render_html()
        rtn += self.render_wins()
        return rtn

