Triplebyte Pentago XL Challenge
===============================

We live in heady times. AI and machine learning are advancing at an incredible rate, and problems that previously seemed intractable are falling to the swords of diligent programmers. DeepMind's AlphaGo, for example, recently defeated world Go champion Lee Sedol. This is impressive. But it's only the beginning. At Triplebyte, we're laser focused on the real challenge: building the worlds best Pentago XL computer. We thus announce the the 1st annual Triplebyte Pentago XL Contest!


Pentago XL
----------
Pentago XL is a four-player extension of the game Pentago. The board is 9x9, and composed of 9 different individually rotating 3x3 tiles. Players take turns placing a colored stone on the board, and rotating one of the 9 tiles by 90 degrees. The game is over when any player has 5 pieces in a row. It is worth noting that the size of the board (9x9) and number of potential rotations (18) give the Pentago XL game tree a higher branching factor than Go! Take that DeepMind!


The Server
-----------
This repository contains the Pentago server that will be used to run the contest. Each contestant must write an AI agent capable of interacting with this server. The protocol is described in the doc protocol.txt. For the convenience of contestants not wishing to write their own networked client, we've written a wrapper client (wrapper_client.py). This client opens a child process, and pipes board positions in through stdin. You may use this to wrap your client.

The Contest
-----------

The contest will have 3 rounds. The 1st round will take place on April 4th, the 2nd on April 18th, and the last and final match on May 2nd. The 1st two rounds are simple training rounds. The AI that wins the most games in the final round, however, we be declared champion, and prizes will be awarded. Each AI will have 15 seconds to complete each move. If an AI does not complete a move within the time limit, it will be skipped, and play will precede to the next AI.



