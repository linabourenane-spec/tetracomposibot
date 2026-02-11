# optimize_open.py
import subprocess
import json
import random
import sys
import os
import re
from multiprocessing import Pool, cpu_count, freeze_support
from pathlib import Path

# Train ONLY robots 0 and 1 (robots 2 and 3 are hard-coded Braitenberg)
# Evolve NN genomes for OPEN mode.

GENOMES_FILE = "current_genomes.json"
BEST_FILE = "best_open.json"
LOG_FILE = "evolution_open_log.csv"

CONFIG_OPEN = "config_Paintwars_open_menad.py"
DISPLAY_MODE = "2"  # 0/1/2

# Open-ish arenas (can include eval arenas if present)
ARENAS_OPEN = [0, 1, 2, 3, 5, 8]
POSITIONS = [False, True]

# NN architecture MUST match robot_menad.py
NUM_INPUTS = 34
HIDDEN = 8
NUM_OUTPUTS = 2
NUM_PARAMS = (NUM_INPUTS * HIDDEN + HIDDEN) + (HIDDEN * NUM_OUTPUTS + NUM_OUTPUTS)  # 298

# Evolution strategy (1+λ)
GENERATIONS = 40
LAMBDA = 24
MUTATION_RATE = 0.20
SIGMA_START = 0.30
SIGMA_MIN = 0.05
SIGMA_DECAY = 0.97
CLIP_MIN, CLIP_MAX = -2.0, 2.0

RE_PAIR = re.compile(r"\[\s*([^\]]+?)\s*=>\s*(\d+)\s*\]")

TRAIN_IDS = ["0", "1"]


def clamp_genome(g):
    return [min(CLIP_MAX, max(CLIP_MIN, float(x))) for x in g]


def random_genome():
    return [random.uniform(-1, 1) for _ in range(NUM_PARAMS)]


def random_team_genomes():
    return {rid: random_genome() for rid in TRAIN_IDS}


def mutate_genome(genome, sigma, mutation_rate):
    g2 = genome[:]
    for i in range(len(g2)):
        if random.random() < mutation_rate:
            g2[i] += random.gauss(0.0, sigma)
    return clamp_genome(g2)


def mutate_team(team_genomes, sigma, mutation_rate):
    return {rid: mutate_genome(team_genomes[rid], sigma, mutation_rate) for rid in TRAIN_IDS}


def write_open_best(team_genomes: dict, filename: str):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({rid: team_genomes[rid] for rid in TRAIN_IDS}, f)


def write_genomes_for_sim(team_genomes: dict, filename: str):
    # robot_menad.py can read nested experts
    data = {
        "open": {rid: team_genomes[rid] for rid in TRAIN_IDS},
        "maze": {rid: team_genomes[rid] for rid in TRAIN_IDS},  # fallback
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f)


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


def fitness(results):
    wins = sum(1 for _, _, r in results if r == "A")
    ties = sum(1 for _, _, r in results if r == "TIE")
    margin = sum(a - o for a, o, _ in results)
    return wins * 10000 + ties * 2000 + margin, wins, ties, margin


def run_one(arena_id, pos, env):
    p = subprocess.run(
        [sys.executable, "tetracomposibot.py", CONFIG_OPEN, str(arena_id), str(pos), DISPLAY_MODE],
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
    idx, champ_team, sigma = args
    cand = mutate_team(champ_team, sigma, MUTATION_RATE)

    pid = os.getpid()
    tmp = f"tmp_open_{pid}_{idx}.json"
    write_genomes_for_sim(cand, tmp)

    env = os.environ.copy()
    env["GENOMES_FILE"] = tmp
    env["FORCE_MODE"] = "open"

    results = [run_one(a, p, env) for a in ARENAS_OPEN for p in POSITIONS]
    fit, w, t, m = fitness(results)

    try:
        os.remove(tmp)
    except OSError:
        pass

    return idx, fit, w, t, m, cand


def log_header():
    if not Path(LOG_FILE).exists():
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("gen,idx,fit,wins,ties,margin,sigma\n")


def log_line(gen, idx, fit, w, t, m, sigma):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{gen},{idx},{fit},{w},{t},{m},{sigma}\n")


def main():
    random.seed()
    log_header()

    champ = random_team_genomes()
    sigma = SIGMA_START

    # baseline
    tmp0 = "tmp_open_baseline.json"
    write_genomes_for_sim(champ, tmp0)
    env0 = os.environ.copy()
    env0["GENOMES_FILE"] = tmp0
    env0["FORCE_MODE"] = "open"
    base_results = [run_one(a, p, env0) for a in ARENAS_OPEN for p in POSITIONS]
    try:
        os.remove(tmp0)
    except OSError:
        pass

    best_fit, w0, t0, m0 = fitness(base_results)
    write_open_best(champ, BEST_FILE)
    print(f"[OPEN GEN 0] fit={best_fit} wins={w0}/{len(ARENAS_OPEN)*len(POSITIONS)} ties={t0} margin={m0} sigma={sigma:.3f}")

    for gen in range(1, GENERATIONS + 1):
        with Pool(processes=min(cpu_count(), LAMBDA)) as pool:
            jobs = [(i, champ, sigma) for i in range(LAMBDA)]
            scored = pool.map(evaluate_candidate, jobs)

        scored.sort(key=lambda x: x[1], reverse=True)
        best_idx, fit, w, t, m, best_team = scored[0]
        log_line(gen, best_idx, fit, w, t, m, sigma)

        if fit > best_fit:
            best_fit = fit
            champ = best_team
            write_open_best(champ, BEST_FILE)
            tag = "  -> NEW BEST"
        else:
            tag = ""

        print(f"[OPEN GEN {gen}] fit={fit} wins={w}/{len(ARENAS_OPEN)*len(POSITIONS)} ties={t} margin={m} sigma={sigma:.3f}{tag}")
        sigma = max(SIGMA_MIN, sigma * SIGMA_DECAY)


if __name__ == "__main__":
    freeze_support()
    main()
