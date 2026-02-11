# arenas_menad.py
# Wrappe arenas.py et ajoute des arènes 5..9 "maze-like" pour généraliser.

import arenas as _base

ARENA_SIZE = 25

def _empty():
    g = [[0 for _ in range(ARENA_SIZE)] for __ in range(ARENA_SIZE)]
    # borders
    for x in range(ARENA_SIZE):
        g[0][x] = 1
        g[ARENA_SIZE-1][x] = 1
    for y in range(ARENA_SIZE):
        g[y][0] = 1
        g[y][ARENA_SIZE-1] = 1
    return g

def _rect(g, x1, y1, x2, y2, v=1):
    # inclusive bounds, clipped
    x1 = max(0, min(ARENA_SIZE-1, x1))
    x2 = max(0, min(ARENA_SIZE-1, x2))
    y1 = max(0, min(ARENA_SIZE-1, y1))
    y2 = max(0, min(ARENA_SIZE-1, y2))
    if x2 < x1: x1, x2 = x2, x1
    if y2 < y1: y1, y2 = y2, y1
    for y in range(y1, y2+1):
        for x in range(x1, x2+1):
            g[y][x] = v

def _hwall(g, y, x1, x2):
    _rect(g, x1, y, x2, y, 1)

def _vwall(g, x, y1, y2):
    _rect(g, x, y1, x, y2, 1)

def _gate_opening(g, x, y, w=1, h=1):
    _rect(g, x, y, x+w-1, y+h-1, 0)

def _arena5():
    # "double couloir" horizontal + piliers
    g = _empty()
    _hwall(g, 6, 2, 22)
    _hwall(g, 18, 2, 22)
    for x in range(4, 22, 4):
        _vwall(g, x, 8, 16)
    # openings
    _gate_opening(g, 12, 6, 1, 1)
    _gate_opening(g, 8, 18, 1, 1)
    return g

def _arena6():
    # "labyrinthe en peigne"
    g = _empty()
    _vwall(g, 7, 2, 22)
    _vwall(g, 17, 2, 22)
    for y in range(4, 22, 3):
        _hwall(g, y, 8, 16)
    # openings
    _gate_opening(g, 7, 12, 1, 1)
    _gate_opening(g, 17, 10, 1, 1)
    return g

def _arena7():
    # couloirs verticaux alternés (maze-ish)
    g = _empty()
    for x in range(3, 22, 3):
        _vwall(g, x, 2, 22)
        # casser des portes alternées
        if (x//3) % 2 == 0:
            _gate_opening(g, x, 5, 1, 2)
            _gate_opening(g, x, 15, 1, 2)
        else:
            _gate_opening(g, x, 9, 1, 2)
            _gate_opening(g, x, 19, 1, 2)
    return g

def _arena8():
    # mix: blocs + couloir central
    g = _empty()
    _rect(g, 3, 3, 10, 10, 1)
    _rect(g, 14, 14, 21, 21, 1)
    _rect(g, 14, 3, 21, 10, 1)
    _rect(g, 3, 14, 10, 21, 1)
    # couloir central
    _gate_opening(g, 11, 2, 3, 21)
    # petites portes
    _gate_opening(g, 10, 7, 2, 1)
    _gate_opening(g, 13, 17, 2, 1)
    return g

def _arena9():
    # "maze donut" : anneau + branches
    g = _empty()
    _rect(g, 5, 5, 19, 19, 1)
    _rect(g, 7, 7, 17, 17, 0)
    # branches internes
    _vwall(g, 12, 7, 17)
    _hwall(g, 12, 7, 17)
    # portes
    _gate_opening(g, 12, 7, 1, 1)
    _gate_opening(g, 7, 12, 1, 1)
    _gate_opening(g, 12, 17, 1, 1)
    _gate_opening(g, 17, 12, 1, 1)
    return g

_EXTRA = {
    5: _arena5,
    6: _arena6,
    7: _arena7,
    8: _arena8,
    9: _arena9,
}

def get_arena(arena_index):
    if arena_index in _EXTRA:
        return _EXTRA[arena_index]()
    return _base.get_arena(arena_index)
