# tiny-chess-01

A 4 KB chess engine in Python for the make.fun tiny-chess-01 bounty.

`main.py` is the packed entrypoint (makefun-compress/v1 LZMA stub around the
readable source). It plays as `python3 -P -s main.py` against the house
environment: 0x88 board, negamax + quiescence, transposition table, killer
moves, null-move pruning, tapered king evaluation, fixed 80,000-node budget.

Practice Elo ~1173 (trials 0-1), above the 1154 final floor.
