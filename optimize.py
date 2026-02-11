import subprocess
import json
import random
import sys
from multiprocessing import Pool, cpu_count
import os
import re
from pathlib import Path

# ---------------------------
# Files
# ---------------------------
GENOMES_FILE = "current_genomes.json"
BEST_FILE = "best_genomes.json"
LOG_FILE = "evolution_log.csv"

# ---------------------------
# Config files (main + optional alt if you use it)
# ---------------------------
CONFIG_MAIN = "config_Paintwars_train.py"
# CONFIG_ALT = "config_Paintwars_train_alt.py"  # optionnel si tu l'utilises
DISPLAY_MODE = "2"  # fastest

# ---------------------------
# NN architecture (must match robot_menad.py)
# ---------------------------
NUM_PARAMS = (25 * 5 + 5) + (5 * 2 + 2)  # 25 -> 5 -> 2

# ---------------------------
# Evolution strategy (1+λ)-ES
# ---------------------------
GENERATIONS = 60
LAMBDA = 24
MUTATION_RATE = 0.20
SIGMA_START = 0.30
SIGMA_MIN = 0.05
SIGMA_DECAY = 0.97
CLIP_MIN, CLIP_MAX = -2.0, 2.0

# Anti-stagnation
STALL_PATIENCE = 8      # nb de générations sans amélioration
SIGMA_BOOST = 1.25      # multiplicateur si stagnation
SIGMA_MAX = 0.8         # cap (évite de partir en chaos)

# ---------------------------
# Curriculum schedule
# ---------------------------
# gen 1..PHASE1: arènes 0..3, pos False/True (8 matchs)
# puis: arènes 0..4, pos False/True (10 matchs)
PHASE1_GENS = 12

ARENAS = [0, 1, 2, 3,4]
POSITIONS = [False, True]

# ---------------------------
# Parsing scores
# ---------------------------
RE_PAIR = re.compile(r"\[\s*([^\]]+?)\s*=>\s*(\d+)\s*\]")


def set_curriculum(gen: int):
    global ARENAS, POSITIONS
    # Tu peux ajuster si tu veux
    if gen <= PHASE1_GENS:
        ARENAS = [0, 1, 2, 3]
        POSITIONS = [False, True]
    else:
        ARENAS = [0, 1, 2, 3, 4]
        POSITIONS = [False, True]


def write_team_genomes(team_genomes: dict, filename: str = GENOMES_FILE):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(team_genomes, f)


def random_genome():
    return [random.uniform(-1, 1) for _ in range(NUM_PARAMS)]


def random_team_genomes():
    return {str(i): random_genome() for i in range(4)}


def mutate_genome(genome, sigma, mutation_rate):
    g2 = genome[:]  # copy
    for i in range(len(g2)):
        if random.random() < mutation_rate:
            g2[i] += random.gauss(0.0, sigma)
            if g2[i] < CLIP_MIN:
                g2[i] = CLIP_MIN
            elif g2[i] > CLIP_MAX:
                g2[i] = CLIP_MAX
    return g2


def mutate_team(team_genomes, sigma, mutation_rate):
    return {k: mutate_genome(v, sigma, mutation_rate) for k, v in team_genomes.items()}


def parse_match(stdout_text: str):
    """
    Robust: ignore "X wins!" text, deduce winner from scores.
    Returns (scoreA, scoreOpp, res) where res in {"A","OPP","TIE"}.
    """
    if not stdout_text:
        return None, None, None

    lines = stdout_text.splitlines()[::-1]
    for line in lines:
        if "=>" not in line:
            continue

        pairs = RE_PAIR.findall(line)
        if not pairs:
            continue

        scores = {team.strip(): int(score) for team, score in pairs}
        if "A" not in scores:
            continue

        opp_team = None
        for t in scores.keys():
            if t != "A":
                opp_team = t
                break
        if opp_team is None:
            continue

        a = scores["A"]
        o = scores[opp_team]

        if a > o:
            return a, o, "A"
        elif a < o:
            return a, o, "OPP"
        else:
            return a, o, "TIE"

    return None, None, None


def fitness_aggregate(results):
    """
    Fitness = wins*10000 + ties*2000 + margin
    """
    wins = 0
    ties = 0
    margin = 0

    for a, o, res in results:
        res_norm = (res or "").strip().upper()
        if res_norm == "A":
            wins += 1
        elif res_norm == "TIE":
            ties += 1
        margin += (a - o)

    fit = wins * 10000 + ties * 2000 + margin
    return fit, wins, ties, margin


def run_one_match(arena_id: int, position: bool, env=None):
    """
    Runs 1 match using CONFIG_MAIN.
    Returns (a, o, res) or CRASH/NOPARSE.
    """
    proc = subprocess.run(
        [sys.executable, "tetracomposibot.py", CONFIG_MAIN, str(arena_id), str(position), DISPLAY_MODE],
        capture_output=True,
        text=True,
        env=env
    )

    if proc.returncode != 0:
        return None, None, "CRASH"

    a, o, res = parse_match(proc.stdout)
    if a is None:
        return None, None, "NOPARSE"

    return a, o, res


def evaluate_team(team_genomes, env=None):
    """
    Returns: fit, wins, ties, margin, details
    details: list of dicts for diagnosis
    """
    if env is None:
        write_team_genomes(team_genomes, GENOMES_FILE)

    match_results = []
    details = []

    for ar in ARENAS:
        for pos in POSITIONS:
            a, o, res = run_one_match(ar, pos, env=env)

            if res in ("CRASH", "NOPARSE"):
                match_results.append((0, 10**6, "OPP"))
                details.append({"arena": ar, "pos": pos, "A": None, "OPP": None, "res": res})
            else:
                match_results.append((a, o, res))
                details.append({"arena": ar, "pos": pos, "A": a, "OPP": o, "res": res})

    fit, wins, ties, margin = fitness_aggregate(match_results)
    return fit, wins, ties, margin, details


def save_best(best_genomes, best_fit, gen, details):
    with open(BEST_FILE, "w", encoding="utf-8") as f:
        json.dump(best_genomes, f)

    # Print what is still lost (very useful)
    losses = [d for d in details if d["res"] != "A"]
    print(f"  -> BEST updated: gen={gen} fitness={best_fit} saved to {BEST_FILE}", flush=True)
    if losses:
        print("     Remaining non-wins:", flush=True)
        for d in losses:
            print(f"       arena={d['arena']} pos={d['pos']} A={d['A']} OPP={d['OPP']} res={d['res']}", flush=True)
    else:
        print("     PERFECT: all matches won ✅", flush=True)


def log_header():
    if not Path(LOG_FILE).exists():
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("generation,kind,index,fitness,wins,ties,margin,sigma\n")


def log_line(gen, kind, idx, fit, wins, ties, margin, sigma):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{gen},{kind},{idx},{fit},{wins},{ties},{margin},{sigma}\n")


def evaluate_child_parallel(args):
    """
    args = (child_index, champion_team, sigma, mutation_rate, arenas, positions)
    Each worker writes current_genomes_<pid>.json, set env GENOMES_FILE.
    """
    idx, champion_team, sigma, mutation_rate, arenas, positions = args

    child = mutate_team(champion_team, sigma=sigma, mutation_rate=mutation_rate)

    pid = os.getpid()
    genomes_file = f"current_genomes_{pid}.json"
    write_team_genomes(child, genomes_file)

    env = os.environ.copy()
    env["GENOMES_FILE"] = genomes_file

    match_results = []
    # local evaluation using passed arenas/positions (avoid sharing globals)
    for ar in arenas:
        for pos in positions:
            a, o, res = run_one_match(ar, pos, env=env)
            if res in ("CRASH", "NOPARSE"):
                match_results.append((0, 10**6, "OPP"))
            else:
                match_results.append((a, o, res))

    fit, wins, ties, margin = fitness_aggregate(match_results)

    try:
        os.remove(genomes_file)
    except OSError:
        pass

    return idx, fit, wins, ties, margin, child


def main():
    random.seed()
    log_header()

    sigma = SIGMA_START
    champion = random_team_genomes()

    # GEN 0 evaluation (phase curriculum gen=0 treated as 1 for schedule)
    set_curriculum(1)
    best_fit, best_w, best_t, best_m, best_details = evaluate_team(champion, env=None)
    save_best(champion, best_fit, gen=0, details=best_details)
    print(f"[GEN 0] champion fitness={best_fit} wins={best_w} ties={best_t} margin={best_m} sigma={sigma:.3f}", flush=True)
    log_line(0, "champion", 0, best_fit, best_w, best_t, best_m, sigma)

    stall = 0  # stagnation counter

    for gen in range(1, GENERATIONS + 1):
        set_curriculum(gen)

        # sigma schedule
        sigma = max(SIGMA_MIN, sigma * SIGMA_DECAY)

        # anti-stagnation
        if stall >= STALL_PATIENCE:
            sigma = min(SIGMA_MAX, sigma * SIGMA_BOOST)
            stall = 0
            print(f"[GEN {gen}] sigma boost -> {sigma:.3f}", flush=True)

        # re-eval champion (stochasticity)
        champ_fit, champ_w, champ_t, champ_m, _ = evaluate_team(champion, env=None)
        log_line(gen, "champion", -1, champ_fit, champ_w, champ_t, champ_m, sigma)

        # evaluate children in parallel with snapshot of curriculum
        arenas_snapshot = list(ARENAS)
        positions_snapshot = list(POSITIONS)

        n_workers = max(1, cpu_count() - 1)
        tasks = [(i, champion, sigma, MUTATION_RATE, arenas_snapshot, positions_snapshot) for i in range(LAMBDA)]

        with Pool(processes=n_workers) as pool:
            results = pool.map(evaluate_child_parallel, tasks)

        best_child_fit = -10**18
        best_child = None
        best_child_stats = None

        for idx, fit, w, t, m, child in results:
            log_line(gen, "child", idx, fit, w, t, m, sigma)
            if fit > best_child_fit:
                best_child_fit = fit
                best_child = child
                best_child_stats = (w, t, m)

        # selection
        if best_child_fit > champ_fit:
            champion = best_child
            champ_fit = best_child_fit
            champ_w, champ_t, champ_m = best_child_stats

        # global best
        if champ_fit > best_fit:
            # compute best details (only when improved)
            best_fit, best_w, best_t, best_m = champ_fit, champ_w, champ_t, champ_m
            _, _, _, _, best_details = evaluate_team(champion, env=None)
            save_best(champion, best_fit, gen=gen, details=best_details)
            stall = 0
        else:
            stall += 1

        print(f"[GEN {gen}] fitness={champ_fit} wins={champ_w} ties={champ_t} margin={champ_m} "
              f"sigma={sigma:.3f} (global best={best_fit}) "
              f"curriculum={arenas_snapshot} pos={positions_snapshot}",
              flush=True)

    print("\n====================")
    print("FIN EVOLUTION")
    print("Best fitness:", best_fit)
    print("Best genomes saved:", BEST_FILE)
    print("Log:", LOG_FILE)


if __name__ == "__main__":
    main()
