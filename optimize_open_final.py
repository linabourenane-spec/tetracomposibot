# optimize_open.py
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
BEST_FILE = "best_open.json"
LOG_FILE = "evolution_open_log.csv"

# ---------------------------
# Config
# ---------------------------
VERBOSE_MATCHES = os.environ.get("VERBOSE_MATCHES", "1") != "0"
VERBOSE_EVERY_GEN = int(os.environ.get("VERBOSE_EVERY_GEN", "1"))
CONFIG_OPEN = "config_Paintwars_open_menad.py"
DISPLAY_MODE = "2"  # fastest (0/1/2)

# ---------------------------
# Arenas
# ---------------------------
# Open-ish (inclut tes nouvelles arènes)
ARENAS_OPEN = [0, 1,3]
POSITIONS = [False, True]

# ---------------------------
# NN architecture (must match robot_menad.py)
# ---------------------------
NUM_INPUTS = 34
HIDDEN = 8
NUM_OUTPUTS = 2
NUM_PARAMS = (NUM_INPUTS * HIDDEN + HIDDEN) + (HIDDEN * NUM_OUTPUTS + NUM_OUTPUTS)  # 298

# ---------------------------
# ES (1+λ)
# ---------------------------
GENERATIONS = 40
LAMBDA = 24
MUTATION_RATE = 0.20
SIGMA_START = 0.30
SIGMA_MIN = 0.05
SIGMA_DECAY = 0.97
CLIP_MIN, CLIP_MAX = -2.0, 2.0

# ---------------------------
# Parsing scores (robuste)
# ---------------------------
RE_PAIR = re.compile(r"\[\s*([^\]]+?)\s*=>\s*(\d+)\s*\]")


def write_team_genomes(team_genomes: dict, filename: str):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(team_genomes, f)


def random_genome():
    return [random.uniform(-1, 1) for _ in range(NUM_PARAMS)]


TRAIN_IDS = ["0", "1"]  # Only train the 2 NN robots


def random_team_genomes():
    # only genomes for robots 0 and 1
    return {rid: random_genome() for rid in TRAIN_IDS}


def mutate_genome(genome, sigma, mutation_rate):
    g2 = genome[:]
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
    DEDUIT le vainqueur uniquement depuis les scores.
    Retour: (scoreA, scoreOpp, res) res in {"A","OPP","TIE"}.
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

        opp = None
        for t in scores.keys():
            if t != "A":
                opp = t
                break
        if opp is None:
            continue

        a = scores["A"]
        o = scores[opp]
        if a > o:
            return a, o, "A"
        elif a < o:
            return a, o, "OPP"
        else:
            return a, o, "TIE"

    return None, None, None


def _tail(text: str, n=12):
    if not text:
        return ""
    lines = text.splitlines()
    return "\n".join(lines[-n:])


def run_one_match(arena_id: int, position: bool, env=None, verbose=True):
    """
    Lance 1 match. Retourne (a,o,res,stdout,stderr,returncode).
    """
    proc = subprocess.run(
        [sys.executable, "tetracomposibot.py", CONFIG_OPEN, str(arena_id), str(position), DISPLAY_MODE],
        capture_output=True,
        text=True,
        env=env
    )

    a, o, res = (None, None, None)
    if proc.returncode == 0:
        a, o, res = parse_match(proc.stdout)

    # Affichage match par match (ce que tu voulais)
    if verbose:
        if proc.returncode != 0:
            print(f"[MATCH] arena={arena_id} pos={position} -> CRASH (code={proc.returncode})", flush=True)
            ts = _tail(proc.stdout, 10)
            te = _tail(proc.stderr, 10)
            if ts:
                print("  stdout tail:\n" + ts, flush=True)
            if te:
                print("  stderr tail:\n" + te, flush=True)
        elif a is None:
            print(f"[MATCH] arena={arena_id} pos={position} -> NOPARSE", flush=True)
            ts = _tail(proc.stdout, 12)
            if ts:
                print("  stdout tail:\n" + ts, flush=True)
        else:
            print(f"[MATCH] arena={arena_id} pos={position} -> A={a} OPP={o} res={res}", flush=True)

    return a, o, res, proc.stdout, proc.stderr, proc.returncode


def fitness_aggregate(results):
    wins = 0
    ties = 0
    margin = 0
    for a, o, res in results:
        rr = (res or "").strip().upper()
        if rr == "A":
            wins += 1
        elif rr == "TIE":
            ties += 1
        margin += (a - o)
    fit = wins * 10000 + ties * 2000 + margin
    return fit, wins, ties, margin


def evaluate_team(team_genomes, verbose_matches=None, env=None):
    """
    Retourne: fit,wins,ties,margin,details
    details: list[{arena,pos,A,OPP,res}]
    """
    if verbose_matches is None:
        verbose_matches = VERBOSE_MATCHES

    if env is None:
        write_team_genomes(team_genomes, GENOMES_FILE)
        env = os.environ.copy()
        env["GENOMES_FILE"] = GENOMES_FILE

    results = []
    details = []
    for ar in ARENAS_OPEN:
        for pos in POSITIONS:
            a, o, res, *_ = run_one_match(ar, pos, env=env, verbose=verbose_matches)

            if res is None:
                # CRASH/NOPARSE -> penalty
                results.append((0, 10**6, "OPP"))
                details.append({"arena": ar, "pos": pos, "A": None, "OPP": None, "res": "CRASH/NOPARSE"})
            else:
                results.append((a, o, res))
                details.append({"arena": ar, "pos": pos, "A": a, "OPP": o, "res": res})

    fit, wins, ties, margin = fitness_aggregate(results)
    return fit, wins, ties, margin, details


def save_best(best_genomes, best_fit, gen, details):
    with open(BEST_FILE, "w", encoding="utf-8") as f:
        json.dump(best_genomes, f)
    print(f"  -> NEW BEST OPEN @gen={gen} fit={best_fit} saved to {BEST_FILE}", flush=True)

    nonwins = [d for d in details if d["res"] != "A"]
    if nonwins:
        print("     Remaining non-wins:", flush=True)
        for d in nonwins:
            print(f"       arena={d['arena']} pos={d['pos']} A={d['A']} OPP={d['OPP']} res={d['res']}", flush=True)
    else:
        print("     PERFECT OPEN ✅", flush=True)


def log_header():
    if not Path(LOG_FILE).exists():
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("generation,kind,index,fitness,wins,ties,margin,sigma\n")


def log_line(gen, kind, idx, fit, wins, ties, margin, sigma):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{gen},{kind},{idx},{fit},{wins},{ties},{margin},{sigma}\n")


def evaluate_child_parallel(args):
    """
    args = (child_index, champion_team, sigma, mutation_rate)
    Chaque worker écrit current_genomes_<pid>.json et set env GENOMES_FILE.
    """
    idx, champion_team, sigma, mutation_rate = args
    child = mutate_team(champion_team, sigma=sigma, mutation_rate=mutation_rate)

    pid = os.getpid()
    genomes_file = f"current_genomes_{pid}.json"
    write_team_genomes(child, genomes_file)

    env = os.environ.copy()
    env["GENOMES_FILE"] = genomes_file

    results = []
    for ar in ARENAS_OPEN:
        for pos in POSITIONS:
            a, o, res, *_ = run_one_match(ar, pos, env=env, verbose=False)
            if res is None:
                results.append((0, 10**6, "OPP"))
            else:
                results.append((a, o, res))

    fit, wins, ties, margin = fitness_aggregate(results)

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

    # GEN 0: on affiche tous les matchs pour debug
    fit0, w0, t0, m0, det0 = evaluate_team(champion, verbose_matches=True)
    save_best(champion, fit0, gen=0, details=det0)
    log_line(0, "champion", 0, fit0, w0, t0, m0, sigma)

    best_fit = fit0

    total_matches = len(ARENAS_OPEN) * len(POSITIONS)
    print(f"[OPEN GEN 0] fit={fit0} wins={w0}/{total_matches} ties={t0} margin={m0} sigma={sigma:.3f}", flush=True)

    for gen in range(1, GENERATIONS + 1):
        sigma = max(SIGMA_MIN, sigma * SIGMA_DECAY)

        # re-eval champion sans spam (mais tu peux mettre True si tu veux)
        champ_fit, champ_w, champ_t, champ_m, _ = evaluate_team(champion, verbose_matches=False)
        log_line(gen, "champion", -1, champ_fit, champ_w, champ_t, champ_m, sigma)

        n_workers = max(1, cpu_count() - 1)
        tasks = [(i, champion, sigma, MUTATION_RATE) for i in range(LAMBDA)]
        with Pool(processes=n_workers) as pool:
            results = pool.map(evaluate_child_parallel, tasks)

        # pick best child
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
        else:
            champ_w, champ_t, champ_m = champ_w, champ_t, champ_m

        # global best -> on imprime détails quand amélioration
        if champ_fit > best_fit:
            best_fit = champ_fit
            det = evaluate_team(champion, verbose_matches=True)[4]  # affiche matchs du nouveau best
            save_best(champion, best_fit, gen=gen, details=det)

        # debug: afficher les matchs du champion régulièrement (pour voir l'évolution)
        if VERBOSE_MATCHES and (gen % VERBOSE_EVERY_GEN == 0) and (champ_fit == best_fit):
            evaluate_team(champion, verbose_matches=True)  # prints [MATCH] lines

        print(
            f"[OPEN GEN {gen}] fit={champ_fit} wins={champ_w}/{total_matches} ties={champ_t} "
            f"margin={champ_m} sigma={sigma:.3f} (global={best_fit})",
            flush=True
        )


if __name__ == "__main__":
    main()
