from robot import *
import math
import json
import os
import random
import re

# ---------- Sensors index ----------
F  = 0
FL = 1
L  = 2
RL = 3
RE = 4
RR = 5
R  = 6
FR = 7

VIEW_NONE  = 0
VIEW_WALL  = 1
VIEW_ROBOT = 2

# ---------- NN hyperparams ----------
NUM_INPUTS = 34
HIDDEN = 8
NUM_OUTPUTS = 2  # (t, r)

GENOMES_FILE = os.environ.get("GENOMES_FILE", "current_genomes.json")
FORCE_MODE = os.environ.get("FORCE_MODE", "").strip().lower()  # "open" / "maze" / ""

def clamp(x, a=-1.0, b=1.0):
    return max(a, min(b, float(x)))

def is_ally(view_i, team_i, my_team):
    return view_i == VIEW_ROBOT and team_i == my_team

def is_enemy(view_i, team_i, my_team):
    return view_i == VIEW_ROBOT and team_i != my_team and team_i != "n/a"

# -------------------------------------------------------------------
# Memory packing (ONE int) :
# mode:0/1, ctx:0..99, esc_dir:0/1, esc_timer:0..99
# mem = mode*1_000_000 + ctx*10_000 + esc_dir*100 + esc_timer
# -------------------------------------------------------------------
def mem_unpack(mem):
    mem = int(mem) if mem is not None else 0
    mode = mem // 1_000_000
    ctx = (mem // 10_000) % 100
    esc_dir = (mem // 100) % 100
    esc_timer = mem % 100
    mode = 0 if mode <= 0 else 1
    ctx = max(0, min(99, ctx))
    esc_dir = 1 if esc_dir else 0
    esc_timer = max(0, min(99, esc_timer))
    return mode, ctx, esc_dir, esc_timer

def mem_pack(mode, ctx, esc_dir, esc_timer):
    mode = 0 if mode <= 0 else 1
    ctx = max(0, min(99, int(ctx)))
    esc_dir = 1 if esc_dir else 0
    esc_timer = max(0, min(99, int(esc_timer)))
    return mode*1_000_000 + ctx*10_000 + esc_dir*100 + esc_timer

# ---------- Simple maze-likeness ----------
def count_close_walls(sensor_view, sensors, thr=0.26):
    c = 0
    for i in range(8):
        if sensor_view[i] == VIEW_WALL and float(sensors[i]) < thr:
            c += 1
    return c

def detect_corridor(sensor_view, sensors):
    left_close = (sensor_view[L] == VIEW_WALL and sensors[L] < 0.35) or (sensor_view[FL] == VIEW_WALL and sensors[FL] < 0.30)
    right_close = (sensor_view[R] == VIEW_WALL and sensors[R] < 0.35) or (sensor_view[FR] == VIEW_WALL and sensors[FR] < 0.30)
    return left_close and right_close

# ---------- NN ----------
class NeuralNetwork:
    def __init__(self, genome=None):
        self.total_params = (NUM_INPUTS*HIDDEN + HIDDEN) + (HIDDEN*NUM_OUTPUTS + NUM_OUTPUTS)
        if genome is None:
            genome = [random.uniform(-0.5, 0.5) for _ in range(self.total_params)]
        else:
            genome = [float(v) for v in genome]

        # Safety: pad/trim
        if len(genome) < self.total_params:
            genome = genome + [random.uniform(-0.05, 0.05) for _ in range(self.total_params - len(genome))]
        elif len(genome) > self.total_params:
            genome = genome[:self.total_params]

        self.genome = genome
        self._unpack()

    def _unpack(self):
        idx = 0
        self.W1 = []
        for _ in range(HIDDEN):
            self.W1.append(self.genome[idx:idx+NUM_INPUTS])
            idx += NUM_INPUTS
        self.b1 = self.genome[idx:idx+HIDDEN]
        idx += HIDDEN
        self.W2 = []
        for _ in range(NUM_OUTPUTS):
            self.W2.append(self.genome[idx:idx+HIDDEN])
            idx += HIDDEN
        self.b2 = self.genome[idx:idx+NUM_OUTPUTS]
        idx += NUM_OUTPUTS

    @staticmethod
    def relu(x):
        return x if x > 0 else 0.0

    def forward(self, x):
        h = []
        for j in range(HIDDEN):
            s = self.b1[j]
            w = self.W1[j]
            for i in range(NUM_INPUTS):
                s += w[i] * x[i]
            h.append(self.relu(s))

        out = []
        for k in range(NUM_OUTPUTS):
            s = self.b2[k]
            w = self.W2[k]
            for j in range(HIDDEN):
                s += w[j] * h[j]
            out.append(math.tanh(s))
        return out  # [-1,1] each

# ---------- Genome loading ----------
def _load_genomes():
    if not os.path.exists(GENOMES_FILE):
        return {}
    try:
        with open(GENOMES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def _get_genome(data, mode, idx):
    key = str(idx)
    # format B: {"open":{...}, "maze":{...}}
    if isinstance(data, dict) and ("open" in data or "maze" in data):
        block = data.get(mode, {})
        if isinstance(block, dict) and key in block:
            return block[key]
        # fallback to open if missing
        block2 = data.get("open", {})
        if isinstance(block2, dict) and key in block2:
            return block2[key]
        return None
    # format A: {"0":[...], "1":[...]}
    if isinstance(data, dict) and key in data:
        return data[key]
    return None

# ---------- Stable Braitenberg behaviours ----------
STEER = {
    F:  0.0,
    FL: +0.6,
    L:  +0.9,
    RL: +1.0,
    RE:  0.0,
    RR: -1.0,
    R:  -0.9,
    FR: -0.6,
}

class Robot_player(Robot):
    team_name = "MenadTeam-NN+BRAIT"
    _cached_genomes = None

    def __init__(self, x, y, theta, name="n/a", team="A"):
        super().__init__(x, y, theta, name=name, team=team)
        self.memory = 0

        m = re.search(r"menad_(\d+)", str(self.name))
        self.idx = int(m.group(1)) if m else (self.id - 1)

        # role for NN input (0 explorer, 1 aggressor)
        self.role = 1.0 if self.idx == 1 else 0.0

        if Robot_player._cached_genomes is None:
            Robot_player._cached_genomes = _load_genomes()

        # NN only for robots 0 and 1
        if self.idx in (0, 1):
            data = Robot_player._cached_genomes
            g_open = _get_genome(data, "open", self.idx)
            g_maze = _get_genome(data, "maze", self.idx)
            self.nn_open = NeuralNetwork(g_open)
            self.nn_maze = NeuralNetwork(g_maze if g_maze is not None else g_open)

    # ----- escape (works for everyone) -----
    def do_escape_if_needed(self, sensors, sensor_view, sensor_team, esc_dir, esc_timer):
        if esc_timer > 0:
            esc_timer -= 1
            rot = +0.85 if esc_dir == 0 else -0.85
            return True, (-0.55, rot), esc_dir, esc_timer

        wall_hard = (sensor_view[F] == VIEW_WALL and sensors[F] < 0.14) \
                    or (sensor_view[FL] == VIEW_WALL and sensors[FL] < 0.12) \
                    or (sensor_view[FR] == VIEW_WALL and sensors[FR] < 0.12)

        ally_hard = (is_ally(sensor_view[F],  sensor_team[F],  self.team) and sensors[F]  < 0.18) \
                    or (is_ally(sensor_view[FL], sensor_team[FL], self.team) and sensors[FL] < 0.16) \
                    or (is_ally(sensor_view[FR], sensor_team[FR], self.team) and sensors[FR] < 0.16)

        if wall_hard or ally_hard:
            esc_dir = 0 if (self.idx % 2 == 0) else 1
            esc_len = 8 if self.idx == 2 else 12
            esc_timer = esc_len
            rot = +0.85 if esc_dir == 0 else -0.85
            return True, (-0.55, rot), esc_dir, esc_timer

        return False, (0.0, 0.0), esc_dir, esc_timer

    # ----- wall follower (robot 2) -----
    def wall_follow_left(self, sensors, sensor_view):
        def wall(i):
            return sensor_view[i] == VIEW_WALL

        f = sensors[F]
        fl = sensors[FL]
        l = sensors[L]
        rl = sensors[RL]

        left_seen = wall(L) or wall(FL) or wall(RL)

        if wall(F) and f < 0.55:
            return 0.80, -0.18

        if left_seen:
            if wall(L):
                d = l
            elif wall(FL):
                d = fl
            else:
                d = rl

            target = 0.30
            err = target - d
            r = max(-0.18, min(0.18, 0.9 * err))
            t = 0.85

            if d < 0.16:
                r = -0.18
                t = 0.80

            return t, r

        return 0.95, 0.0  # arena open: go straight until border

    # ----- hunter (robot 3) -----
    def hunter(self, sensors, sensor_view, sensor_robot, sensor_team):
        # anti-corner
        front_wall = (sensor_view[F] == VIEW_WALL and sensors[F] < 0.55)
        fl_wall = (sensor_view[FL] == VIEW_WALL and sensors[FL] < 0.35)
        fr_wall = (sensor_view[FR] == VIEW_WALL and sensors[FR] < 0.35)

        if front_wall and (fl_wall or fr_wall):
            if fl_wall and not fr_wall:
                return -0.35, -0.35
            if fr_wall and not fl_wall:
                return -0.35, +0.35
            return -0.35, (+0.35 if self.idx % 2 == 0 else -0.35)

        # anti-wall early
        if sensor_view[F] == VIEW_WALL and sensors[F] < 0.75:
            left_free  = sensors[FL] if sensor_view[FL] != VIEW_WALL else 0.0
            right_free = sensors[FR] if sensor_view[FR] != VIEW_WALL else 0.0
            t = 0.80
            r = -0.18 if right_free > left_free else +0.18  # r- = right, r+ = left
            return t, r

        # chase enemy
        best_i = None
        best_d = 1.0
        for i in range(8):
            if is_enemy(sensor_view[i], sensor_team[i], self.team):
                if sensors[i] < best_d:
                    best_d = sensors[i]
                    best_i = i

        if best_i is not None:
            r = STEER.get(best_i, 0.0)
            if best_d > 0.45:
                t = 0.85
            elif best_d > 0.25:
                t = 0.70
            else:
                t = 0.45
            return clamp(t), clamp(r)

        # explore fast
        t = 0.95
        r = +0.08 if (self.idx % 2 == 0) else -0.08

        if sensor_view[L] == VIEW_WALL and sensors[L] < 0.28:
            r = -0.16
        elif sensor_view[R] == VIEW_WALL and sensors[R] < 0.28:
            r = +0.16

        if sensor_view[FL] == VIEW_WALL and sensors[FL] < 0.35:
            r = -0.16
        if sensor_view[FR] == VIEW_WALL and sensors[FR] < 0.35:
            r = +0.16

        if (sensor_view[L] == VIEW_WALL and sensors[L] < 0.22) and (sensor_view[R] == VIEW_WALL and sensors[R] < 0.22):
            t = 0.80

        return clamp(t), clamp(r)

    # ----- NN input vector (34) -----
    def nn_inputs34(self, sensors, sensor_view, sensor_team, ctx_norm, role):
        x = []
        # 8 distances (clipped)
        for i in range(8):
            x.append(min(1.0, float(sensors[i])))

        # 8 walls
        for i in range(8):
            x.append(1.0 if sensor_view[i] == VIEW_WALL else 0.0)

        # 8 allies
        for i in range(8):
            x.append(1.0 if is_ally(sensor_view[i], sensor_team[i], self.team) else 0.0)

        # 8 enemies
        for i in range(8):
            x.append(1.0 if is_enemy(sensor_view[i], sensor_team[i], self.team) else 0.0)

        # ctx + role
        x.append(float(ctx_norm))
        x.append(float(role))
        return x

    # ----- mode/ctx update -----
    def update_mode_ctx(self, mode, ctx, sensor_view, sensors):
        many = (count_close_walls(sensor_view, sensors, thr=0.26) >= 3)
        corridor = detect_corridor(sensor_view, sensors)
        front_hit = (sensor_view[F] == VIEW_WALL and sensors[F] < 0.14)

        if front_hit:
            ctx = min(99, ctx + 6)
        elif many or corridor:
            ctx = min(99, ctx + 2)
        else:
            ctx = max(0, ctx - 1)

        if FORCE_MODE == "open":
            mode = 0
        elif FORCE_MODE == "maze":
            mode = 1
        else:
            # hysteresis
            if mode == 0 and ctx >= 60:
                mode = 1
            elif mode == 1 and ctx <= 40:
                mode = 0
        return mode, ctx

    def step(self, sensors, sensor_view=None, sensor_robot=None, sensor_team=None):
        if self.team != "A":
            return 0.0, 0.0, False

        mode, ctx, esc_dir, esc_timer = mem_unpack(self.memory)

        # update ctx/mode (even for brait, harmless)
        mode, ctx = self.update_mode_ctx(mode, ctx, sensor_view, sensors)
        ctx_norm = ctx / 99.0

        # escape first (prevents blocks for all robots)
        esc, (t, r), esc_dir, esc_timer = self.do_escape_if_needed(sensors, sensor_view, sensor_team, esc_dir, esc_timer)
        if esc:
            self.memory = mem_pack(mode, ctx, esc_dir, esc_timer)
            return t, r, False

        # robot roles
        if self.idx == 2:
            t, r = self.wall_follow_left(sensors, sensor_view)
            self.memory = mem_pack(mode, ctx, esc_dir, esc_timer)
            return clamp(t), clamp(r), False

        if self.idx == 3:
            t, r = self.hunter(sensors, sensor_view, sensor_robot, sensor_team)
            self.memory = mem_pack(mode, ctx, esc_dir, esc_timer)
            return clamp(t), clamp(r), False

        # NN robots (0 and 1)
        if self.idx in (0, 1):
            x = self.nn_inputs34(sensors, sensor_view, sensor_team, ctx_norm, self.role)
            if mode == 0:
                out = self.nn_open.forward(x)
            else:
                out = self.nn_maze.forward(x)

            # map outputs
            t_raw, r_raw = out[0], out[1]

            # translation: keep forward most of the time (avoid useless reverse)
            t = (t_raw + 1.0) * 0.5  # -> [0,1]
            t = max(0.10, min(1.0, t))

            # rotation: keep as [-1,1] but limit to avoid spins
            r = clamp(r_raw, -0.35, 0.35)

            self.memory = mem_pack(mode, ctx, esc_dir, esc_timer)
            return clamp(t), clamp(r), False

        # fallback (shouldn't happen)
        self.memory = mem_pack(mode, ctx, esc_dir, esc_timer)
        return 0.55, 0.0, False
