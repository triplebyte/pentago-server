Clients communicate with the Pentago server via the following simple line-based protocol


Message Structure
=================

Each message consists of one more more lines, followed by a blank line to mark the end of the message. All lines are terminated with a single '\n' character. The 1st line of each message is the action, and subsequent lines are 0 or more parameters.

For example, a message might look like

JOIN
Bob
match1

This would be serialized as

"JOIN\nBob\nmatch1\n\n"


Specific Messages
=================

JOIN
$name
$room_id

This message is sent from the client to the server.  When a client joins the server, the first message they MUST send is the join message. This take the form

$name is name that they will have on the server. This must be unique. $room_id is the id of the game room that they wish to join. Players in this room (once enough have joined) will be matched in 1 or more games. If a game room with a specified id does not exist, the server will create one

INFO
$text

This message is sent from the server to the client, when it has a message to display about the game state. $text is the message


GAME_STARTED
$piece_i $player_i

This message is sent from the server to the client when a game starts. The parameters are a list of all the players in the game. Each line starts with a player's order of play in the game (1 through 4) followed by the player's name


MAKE_MOVE
$play_time
$board_state

This message is sent from the server to a client, to request that that client make a move. The $play_time  is the time limit (in seconds) that the client has to move, before timing out. The $board_state is a white-space separated list of 81 integers, representing the current game state, serialized row by row, starting in the top left.


BAD_MOVE
$play_time
$board_state

This message is sent (server to client) when the server had rejected a client's move. It has the same params as MAKE_MOVE. The client should send another MOVE message


PLAY
$x $y $rx $rx $rotation

This message is sent from a client to the server to make a move. All the params are white-space separated, on a single line. $x ans $y are the location at which to drop a stone (before any rotations have been applied) 0 <= $x,$y <= 8. $rx and $rx are the coordinates of the tile to rotate. All coordinates use the top left as origin. 0 <= $rx,$ry <= 2. $rotation is either the character "r" or "l". "r" specifies a right or clockwise rotation, while "l" is a left of counterclockwise rotation.


PLAYER_MOVED
$name
$board_state

This message is sent from the server to a client to tell them that a player (including themselves) had moved. $name is the name of the player that moved. $board_state is the resulting board state, in the same format as in the MAKE_MOVE message


PLAYER_LEFT_GAME
$name

This is send to client when another player leaves the game. $name is the name of the player who left


GAME_OVER
$winner1
$winner1

This message is sent to the client when the game is over. One winner parameters will be present for every player how finished the game with at least 5 stones in a row. In the case of a draw, there will be no winner parameters.
