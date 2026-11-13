# tiny chess engine v3: 0x88, negamax+qsearch, TT, killers, null-move, tapered king
import json, os, sys, urllib.request as _u, urllib.error as _e

U = os.environ.get("MAKEFUN_ENV_URL") or sys.exit("MAKEFUN_ENV_URL is not set")

def post(p, b):
    q = _u.Request(U + p, data=json.dumps(b).encode(), headers={"content-type": "application/json"})
    try:
        with _u.urlopen(q) as r:
            return json.load(r)
    except _e.HTTPError as x:
        sys.exit(f"{p}: HTTP {x.code} {x.read().decode(errors='replace')}")

# pieces: 1 P, 2 N, 3 B, 4 R, 5 Q, 6 K; white +, black -
VAL = [0, 100, 320, 330, 500, 900, 0]
KN = [31, 33, 14, 18, -18, -14, -33, -31]      # knight offsets in 0x88
KI = [15, 16, 17, 1, -1, -15, -16, -17]        # king offsets
SL = [(15, 17, -15, -17), (16, 1, -16, -1)]   # bishop dirs, rook dirs

import random
_R = random.Random(20261113)
Z = [[_R.getrandbits(64) for _ in range(128)] for _ in range(13)]
ZS = _R.getrandbits(64)

H = 0

def F(fen):
    global H
    parts = fen.split()
    b = [0] * 128
    rows = parts[0].split("/")
    for i, row in enumerate(rows):
        f = 0
        for c in row:
            if c.isdigit():
                f += int(c)
            else:
                code = "PNBRQK".index(c.upper()) + 1
                b[(7 - i) * 16 + f] = code if c.isupper() else -code
                f += 1
    side = 1 if parts[1] == "w" else -1
    cast = 0
    if len(parts) > 2:
        for c in parts[2]:
            if c in "KQkq":
                cast |= 1 << "KQkq".index(c)
    ep = -1
    if len(parts) > 3 and parts[3] != "-":
        ep = (8 - int(parts[3][1])) * 16 + (ord(parts[3][0]) - 97)
    H = 0
    for i, p in enumerate(b):
        if p:
            H ^= Z[p + 6][i]
    if side < 0:
        H ^= ZS
    if cast:
        H ^= Z[12][64 + cast]
    if ep >= 0:
        H ^= Z[12][ep]
    return b, side, cast, ep

def A(b, sq, by):
    # by: +1 white attacks, -1 black attacks
    for d in KN:
        t = sq + d
        if not t & 0x88 and b[t] == by * 2:
            return True
    for d in KI:
        t = sq + d
        if not t & 0x88 and b[t] == by * 6:
            return True
    # pawns: a white pawn on sq-15/sq-17 attacks sq (white moves up, +16)
    for d in (15, 17):
        t = sq - by * d
        if not t & 0x88 and b[t] == by * 1:
            return True
    for dirs, codes in ((SL[0], (3, 5)), (SL[1], (4, 5))):
        for d in dirs:
            t = sq + d
            while not t & 0x88:
                p = b[t]
                if p:
                    if p * by > 0 and abs(p) in codes:
                        return True
                    break
                t += d
    return False

def K(b, side):
    for i, p in enumerate(b):
        if p == side * 6:
            return i
    return -1

def G(b, side, cast, ep, caps_only=False):
    moves = []
    for f in range(128):
        if f & 0x88:
            continue
        p = b[f]
        if p * side <= 0:
            continue
        a = abs(p)
        if a == 1:
            d = 16 * side
            t = f + d
            if not t & 0x88 and not b[t] and not caps_only:
                if (t >> 4) in (0, 7):
                    for pr in (5, 4, 3, 2):
                        moves.append((f, t, pr, 0, 0))
                else:
                    moves.append((f, t, 0, 0, 0))
                    t2 = f + 2 * d
                    if ((f >> 4) == (1 if side > 0 else 6)) and not b[t2]:
                        moves.append((f, t2, 0, 0, 0))
            for dd in (d - 1, d + 1):
                t = f + dd
                if t & 0x88:
                    continue
                if b[t] * side < 0:
                    if (t >> 4) in (0, 7):
                        for pr in (5, 4, 3, 2):
                            moves.append((f, t, pr, b[t], 0))
                    else:
                        moves.append((f, t, 0, b[t], 0))
                elif t == ep and ep >= 0:
                    moves.append((f, t, 0, -side, 1))
        elif a in (2, 6):
            for d in (KN if a == 2 else KI):
                t = f + d
                if t & 0x88:
                    continue
                if b[t] * side <= 0 and (b[t] or not caps_only):
                    moves.append((f, t, 0, b[t], 0))
            if a == 6 and not caps_only:
                # castling: rights K=bit0,Q=bit1 (white), k=bit2,q=bit3 (black)
                row = 0 if side > 0 else 112
                ks, qs = (1, 2) if side > 0 else (4, 8)
                if cast & ks and not b[row + 5] and not b[row + 6] and b[row + 7] == side * 4 \
                        and not A(b, row + 4, -side) and not A(b, row + 5, -side) and not A(b, row + 6, -side):
                    moves.append((row + 4, row + 6, 0, 0, 2))
                if cast & qs and not b[row + 3] and not b[row + 2] and not b[row + 1] and b[row] == side * 4 \
                        and not A(b, row + 4, -side) and not A(b, row + 3, -side) and not A(b, row + 2, -side):
                    moves.append((row + 4, row + 2, 0, 0, 2))
        else:
            for d in (SL[0] if a == 3 else SL[1] if a == 4 else SL[0] + SL[1]):
                t = f + d
                while not t & 0x88:
                    if b[t] * side <= 0 and (b[t] or not caps_only):
                        moves.append((f, t, 0, b[t], 0))
                    if b[t]:
                        break
                    t += d
    return moves

def do(b, m, side, cast, ep):
    global H
    f, t, pr, cap, fl = m
    p = b[f]
    undo = (f, t, b[t], cap, cast, ep, fl, H)
    H ^= Z[p + 6][f] ^ Z[(pr * side if pr else p) + 6][t]
    if cap:
        H ^= Z[cap + 6][t if fl != 1 else t - 16 * side]
    if fl == 2:
        rf = f + 3 if t > f else f - 4
        rt = f + 1 if t > f else f - 1
        H ^= Z[side * 4 + 6][rf] ^ Z[side * 4 + 6][rt]
    if ep >= 0:
        H ^= Z[12][ep]
    b[t] = pr * side if pr else p
    b[f] = 0
    if fl == 1:  # en passant: remove the pawn beside the target
        b[t - 16 * side] = 0
    elif fl == 2:  # castling: move the rook
        if t > f:
            b[f + 1] = b[f + 3]
            b[f + 3] = 0
        else:
            b[f - 1] = b[f - 4]
            b[f - 4] = 0
    # update castling rights
    old_cast = cast
    if abs(p) == 6:
        cast &= ~(3 if side > 0 else 12)
    if f in (0, 7, 112, 119) or t in (0, 7, 112, 119):
        for sq, bit in ((7, 1), (0, 2), (119, 4), (112, 8)):
            if f == sq or t == sq:
                cast &= ~bit
    if cast != old_cast:
        if old_cast:
            H ^= Z[12][64 + old_cast]
        if cast:
            H ^= Z[12][64 + cast]
    ep2 = -1
    if abs(p) == 1 and abs(t - f) == 32:
        ep2 = (f + t) // 2
    if ep2 >= 0:
        H ^= Z[12][ep2]
    H ^= ZS
    return undo, cast, ep2

def undo(b, m, side, u):
    global H
    f, t, old_t, cap, cast, ep, fl, old_h = u
    H = old_h
    p = b[t]
    b[f] = p
    if m[2]:  # promotion: restore pawn
        b[f] = side * 1
    b[t] = old_t
    if fl == 1:
        b[t - 16 * side] = -side
    elif fl == 2:
        if t > f:
            b[f + 3] = b[f + 1]
            b[f + 1] = 0
        else:
            b[f - 4] = b[f - 1]
            b[f - 1] = 0
    return cast, ep

def P(code, sq, side):
    # square from the moving side's perspective: file 0-7, rank 0-7 (0 = own back rank)
    f = sq & 7
    r = (sq >> 4) if side > 0 else 7 - (sq >> 4)
    cf = 3 - abs(f - 3.5)
    cr = 3 - abs(r - 3.5)
    cen = cf + cr
    if code == 1:
        return 6 * r + (4 if r >= 4 else 0) + (2 if 2 <= f <= 5 else 0)
    if code == 2:
        return 8 * cen
    if code == 3:
        return 6 * cen
    if code == 4:
        return 4 * cen + (12 if r == 6 else 0)
    if code == 5:
        return 4 * cen
    return -6 * cen if True else 0  # king middlegame: stay back

def E(b, side):
    s = 0
    nb = 0
    for sq in range(128):
        if sq & 0x88:
            continue
        p = b[sq]
        if not p:
            continue
        a = abs(p)
        v = VAL[a]
        s += v if p > 0 else -v
        if a == 6:
            f = sq & 7
            r = (sq >> 4) if p > 0 else 7 - (sq >> 4)
            cen = (3 - abs(f - 3.5)) + (3 - abs(r - 3.5))
            w = max(0.0, min(1.0, (4 - nb) / 3.0))  # 0 middlegame -> 1 endgame
            kb = (-6 + 14 * w) * cen
            s += kb if p > 0 else -kb
            continue
        s += P(a, sq, 1 if p > 0 else -1) * (1 if p > 0 else -1)
        if a in (3, 4, 5):
            nb += 1
    # bishop pair
    wb = sum(1 for sq in range(128) if b[sq] == 3)
    bb = sum(1 for sq in range(128) if b[sq] == -3)
    if wb >= 2:
        s += 30
    if bb >= 2:
        s -= 30
    return s if side > 0 else -s

class Engine:
    def __init__(self, budget=80000):
        self.budget = budget
        self.nodes = 0
        self.tt = {}
        self.kill = {}

    def order(self, b, moves, tt_move, ply):
        kl = self.kill.get(ply, ())
        def key(m):
            v = 0
            if tt_move and m == tt_move:
                v = 100000
            elif m[3]:
                v = 10000 + VAL[abs(m[3])] * 10 - VAL[abs(b[m[0]])]
            elif m in kl:
                v = 5000 - kl.index(m)
            return -v
        moves.sort(key=key)
        return moves

    def search(self, b, side, cast, ep, depth, alpha, beta, ply):
        global H
        self.nodes += 1
        if self.nodes > self.budget:
            raise StopIteration
        if depth <= 0:
            return self.qsearch(b, side, cast, ep, alpha, beta, ply)
        # TT probe (H is the incremental zobrist hash)
        h = H
        ent = self.tt.get(h)
        tt_move = None
        if ent and ent[0] >= depth:
            d0, s0, fl0, m0 = ent
            tt_move = m0
            if fl0 == 0:
                return s0
            if fl0 == 1 and s0 >= beta:
                return s0
            if fl0 == 2 and s0 <= alpha:
                return s0
        ks = K(b, side)
        in_check = ks >= 0 and A(b, ks, -side)
        if in_check:
            depth += 1  # check extension
        # null-move pruning
        if depth >= 3 and not in_check and beta < 100000:
            st = E(b, side)
            if st >= beta:
                _sv = H
                H ^= ZS
                if ep >= 0:
                    H ^= Z[12][ep]
                sc = -self.search(b, -side, cast, -1, depth - 3, -beta, -beta + 1, ply + 1)
                H = _sv
                if sc >= beta:
                    return beta
        moves = G(b, side, cast, ep)
        moves = self.order(b, moves, tt_move, ply)
        best = None
        legal = 0
        orig_alpha = alpha
        for m in moves:
            u, c2, e2 = do(b, m, side, cast, ep)
            ks = K(b, side)
            if ks < 0 or A(b, ks, -side):
                undo(b, m, side, u)
                continue
            legal += 1
            try:
                sc = -self.search(b, -side, c2, e2, depth - 1, -beta, -alpha, ply + 1)
            except StopIteration:
                undo(b, m, side, u)
                raise
            undo(b, m, side, u)
            if sc > alpha:
                alpha = sc
                best = m
                if alpha >= beta:
                    if not m[3]:
                        kl = self.kill.setdefault(ply, [])
                        if m not in kl:
                            kl.insert(0, m)
                            del kl[2:]
                    break
        if legal == 0:
            ks = K(b, side)
            if ks >= 0 and A(b, ks, -side):
                return -100000 + ply
            return 0
        # TT store
        if len(self.tt) > 500000:
            self.tt.clear()
        fl = 0 if alpha > orig_alpha and alpha < beta else (1 if alpha >= beta else 2)
        self.tt[h] = (depth, alpha, fl, best)
        return alpha

    def qsearch(self, b, side, cast, ep, alpha, beta, ply):
        self.nodes += 1
        if self.nodes > self.budget:
            raise StopIteration
        ks = K(b, side)
        in_check = ks >= 0 and A(b, ks, -side)
        if not in_check:
            stand = E(b, side)
            if stand >= beta:
                return beta
            if stand > alpha:
                alpha = stand
        moves = G(b, side, cast, ep, caps_only=not in_check)
        moves = self.order(b, moves, None, ply)
        for m in moves:
            u, c2, e2 = do(b, m, side, cast, ep)
            ks2 = K(b, side)
            if ks2 < 0 or A(b, ks2, -side):
                undo(b, m, side, u)
                continue
            try:
                sc = -self.qsearch(b, -side, c2, e2, -beta, -alpha, ply + 1)
            except StopIteration:
                undo(b, m, side, u)
                raise
            undo(b, m, side, u)
            if sc > alpha:
                alpha = sc
                if alpha >= beta:
                    break
        return alpha

    def best_move(self, fen, legal_uci):
        b, side, cast, ep = F(fen)
        root = G(b, side, cast, ep)
        ok = []
        for m in root:
            u, c2, e2 = do(b, m, side, cast, ep)
            ks = K(b, side)
            if ks >= 0 and not A(b, ks, -side):
                ok.append(m)
            undo(b, m, side, u)
        if not ok:
            return legal_uci[0]
        ok = self.order(b, ok, None, 0)
        best = ok[0]
        self.nodes = 0
        try:
            for depth in range(1, 30):
                alpha = -10 ** 9
                cur_best = best
                for m in ok:
                    u, c2, e2 = do(b, m, side, cast, ep)
                    sc = -self.search(b, -side, c2, e2, depth - 1, -10 ** 9, -alpha, 1)
                    undo(b, m, side, u)
                    if sc > alpha:
                        alpha = sc
                        cur_best = m
                best = cur_best
                if self.nodes > self.budget:
                    break
        except StopIteration:
            pass
        f, t, pr, cap, fl = best
        uci = "abcdefgh"[f & 7] + str((f >> 4) + 1) + "abcdefgh"[t & 7] + str((t >> 4) + 1)
        if pr:
            uci = uci[:4] + {5: "q", 4: "r", 3: "b", 2: "n"}[pr]
        if uci not in legal_uci:
            return legal_uci[0]
        return uci

def main():
    eng = Engine(budget=80000)
    while True:
        g = post("/game", {})
        if g["status"] == "done":
            break
        while g["status"] == "your_move":
            mv = eng.best_move(g["fen"], g["legal_moves"])
            g = post("/move", {"game": g["game"], "move": mv})

if __name__ == "__main__":
    main()
