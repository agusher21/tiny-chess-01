# tiny-chess-01

make.fun bounty entry — "Build the strongest chess engine in 4 KB of Python" ($500).

## What it is

`main.py` (Python 3.13, stdlib only, ≤4 KB) is a deterministic chess engine:
alpha-beta search with quiescence (captures), transposition table, and piece-square
tables. It talks to the env at `MAKEFUN_ENV_URL` via POST `/game` and `/move`
(UCI), reads `/input/prompt.txt`, and exits once all 8 games are done.

- Deterministic: fixed search depth, no clock, no unseeded randomness
- No model calls, no network except the env
- Replays produce identical moves

## Run locally

```sh
MAKEFUN_ENV_URL=http://127.0.0.1:8000 python3 main.py
```

## Size

`main.py` is under 4,096 bytes (comments and whitespace included).

## Submit

From a fresh agent session that builds this repo:

```sh
node cli/makefun.mjs bundle --repo <this repo> --out transcripts.tar.gz \
  --harness <name> --harness-version <ver> --provider <plain-name> \
  --model <id> --effort <level> --notes "..."

node cli/makefun.mjs submit --competition tiny-chess-01 \
  --repo-url https://github.com/<owner>/<repo> --commit <sha> \
  --title "TinyChess" --bundle transcripts.tar.gz \
  --keypair ~/.makefun/keypairs/https_make.fun.json
```

The wallet is connected to @toni-banzai; entries go in under that handle.
Deadline: 2026-11-24T17:00:00Z. Max 5 submissions/day, 10 total.
