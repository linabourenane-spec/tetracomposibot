# optimize_maze.py
import subprocess, json, random, sys, os, re
from multiprocessing import Pool, cpu_count, freeze_support
from pathlib import Path

CONFIG = "config_Paintwars_train.py"
DISPLAY_MODE = "2"

# Match-by-match debug
VERBOSE_MATCHES = os.environ.get("VERBOSE_MATCHES", "0") != "0"
VERBOSE_EVERY_GEN = int(os.environ.get("VERBOSE_EVERY_GEN", "5"))

OUT_FILE = "best_maze.json"
LOG_FILE = "evolution_maze.csv"

# Maze-ish arenas
ARENAS = [2,4, 5, 6, 7]
POSITIONS = [False, True]

NUM_INPUTS = 34
HIDDEN = 8
NUM_PARAMS = (NUM_INPUTS * HIDDEN + HIDDEN) + (HIDDEN * 2 + 2)

GENERATIONS = 60
LAMBDA = 24
MUT_RATE = 0.20
SIGMA_START = 0.30
SIGMA_MIN = 0.06
SIGMA_DECAY = 0.97
CLIP_MIN, CLIP_MAX = -2.0, 2.0

RE_PAIR = re.compile(r"\[\s*([^\]]+?)\s*=>\s*(\d+)\s*\]")

def parse_match(stdout_text: str):
    if not stdout_text:
        return None, None, None
    lines = stdout_text.splitlines()[::-1]
    for line in lines:
        if "=>" not in line:
            continue
        pairs = RE_PAIR.findall(line)
        if not pairs:
            continue
        scores = {t.strip(): int(s) for t, s in pairs}
        if "A" not in scores:
            continue
        opp = next((k for k in scores.keys() if k != "A"), None)
        if not opp:
            continue
        a, o = scores["A"], scores[opp]
        if a > o:
            return a, o, "A"
        if a < o:
            return a, o, "OPP"
        return a, o, "TIE"
    return None, None, None


def _tail(text: str, n=12):
    if not text:
        return ""
    lines = text.splitlines()
    return "\n".join(lines[-n:])

def run_one_verbose(arena_id, pos, env):
    p = subprocess.run(
        [sys.executable, "tetracomposibot.py", CONFIG, str(arena_id), str(pos), DISPLAY_MODE],
        capture_output=True,
        text=True,
        env=env
    )
    if p.returncode != 0:
        print(f"[MATCH] arena={arena_id} pos={pos} -> CRASH (code={p.returncode})", flush=True)
        te = _tail(p.stderr, 10)
        if te:
            print("  stderr tail:\n" + te, flush=True)
        return (0, 10**6, "OPP")

    a, o, r = parse_match(p.stdout)
    if a is None:
        print(f"[MATCH] arena={arena_id} pos={pos} -> NOPARSE", flush=True)
        ts = _tail(p.stdout, 12)
        if ts:
            print("  stdout tail:\n" + ts, flush=True)
        return (0, 10**6, "OPP")

    print(f"[MATCH] arena={arena_id} pos={pos} -> A={a} OPP={o} res={r}", flush=True)
    return (a, o, r)

def fitness(results):
    wins = sum(1 for _,_,r in results if r=="A")
    ties = sum(1 for _,_,r in results if r=="TIE")
    margin = sum(a-o for a,o,_ in results)
    return wins*10000 + ties*2000 + margin, wins, ties, margin

def rand_genome():
    return [random.uniform(-1, 1) for _ in range(NUM_PARAMS)]

def clamp_genome(g):
    return [min(CLIP_MAX, max(CLIP_MIN, x)) for x in g]

def mutate(g, sigma):
    out = g[:]
    for i in range(len(out)):
        if random.random() < MUT_RATE:
            out[i] = out[i] + random.gauss(0.0, sigma)
    return clamp_genome(out)

def write_genomes_file(gen0, gen1, path):
    data = {
        "open": {"0": gen0, "1": gen1},  # fallback
        "maze": {"0": gen0, "1": gen1},
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)

def run_one(arena_id, pos, env):
    p = subprocess.run(
        [sys.executable, "tetracomposibot.py", CONFIG, str(arena_id), str(pos), DISPLAY_MODE],
        capture_output=True,
        text=True,
        env=env
    )
    if p.returncode != 0:
        return (0, 10**6, "OPP")
    a, o, r = parse_match(p.stdout)
    if a is None:
        return (0, 10**6, "OPP")
    return (a, o, r)

def evaluate_candidate(args):
    idx, champ0, champ1, sigma = args
    g0 = mutate(champ0, sigma)
    g1 = mutate(champ1, sigma)

    pid = os.getpid()
    tmp = f"tmp_maze_{pid}.json"
    write_genomes_file(g0, g1, tmp)

    env = os.environ.copy()
    env["GENOMES_FILE"] = tmp
    env["FORCE_MODE"] = "maze"

    results = [run_one(a, p, env) for a in ARENAS for p in POSITIONS]
    fit, w, t, m = fitness(results)

    try: os.remove(tmp)
    except OSError: pass

    return idx, fit, w, t, m, g0, g1

def log_header():
    if not Path(LOG_FILE).exists():
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("gen,idx,fit,wins,ties,margin,sigma\n")

def log_line(gen, idx, fit, w, t, m, sigma):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{gen},{idx},{fit},{w},{t},{m},{sigma}\n")


def replay_verbose(gen0, gen1, tag="CHAMP"):
    tmp = f"tmp_replay_{os.getpid()}.json"
    write_genomes_file(gen0, gen1, tmp)
    env = os.environ.copy()
    env["GENOMES_FILE"] = tmp
    env["FORCE_MODE"] = "maze"
    print(f"\n[{tag}] Match details:", flush=True)
    results = [run_one_verbose(a, p, env) for a in ARENAS for p in POSITIONS]
    try: os.remove(tmp)
    except OSError: pass
    return results


def main():
    random.seed()
    log_header()

    champ0, champ1 = rand_genome(), rand_genome()
    best_fit = -10**18
    sigma = SIGMA_START

    for gen in range(GENERATIONS + 1):
        sigma = max(SIGMA_MIN, sigma * (SIGMA_DECAY if gen > 0 else 1.0))

        n_workers = max(1, cpu_count() - 1)
        tasks = [(i, champ0, champ1, sigma) for i in range(LAMBDA)]
        with Pool(processes=n_workers) as pool:
            res = pool.map(evaluate_candidate, tasks)

        res.sort(key=lambda x: x[1], reverse=True)
        idx, fit, w, t, m, g0, g1 = res[0]
        log_line(gen, idx, fit, w, t, m, sigma)

        champ0, champ1 = g0, g1

        if fit > best_fit:
            best_fit = fit
            write_genomes_file(champ0, champ1, OUT_FILE)
            print(f"  -> NEW BEST MAZE @gen={gen} fit={best_fit}")
            if VERBOSE_MATCHES:
                replay_verbose(champ0, champ1, tag=f"NEW BEST gen={gen}")

        print(f"[MAZE GEN {gen}] fit={fit} wins={w}/{len(ARENAS)*len(POSITIONS)} ties={t} margin={m} sigma={sigma:.3f} (global={best_fit})")
        if VERBOSE_MATCHES and (gen % VERBOSE_EVERY_GEN == 0):
            replay_verbose(champ0, champ1, tag=f"REPLAY gen={gen}")

    print("\nSaved:", OUT_FILE)

if __name__ == "__main__":
    freeze_support()
    main()
