# merge_genomes.py
import json

OPEN_FILE = "best_open.json"
MAZE_FILE = "best_maze.json"

BEST_OUT = "best_genomes.json"
CURRENT_OUT = "current_genomes.json"

TRAIN_IDS = ["0", "1"]

def main():
    with open(OPEN_FILE, "r", encoding="utf-8") as f:
        open_g = json.load(f)
    with open(MAZE_FILE, "r", encoding="utf-8") as f:
        maze_g = json.load(f)

    open_map = {rid: open_g[rid] for rid in TRAIN_IDS if rid in open_g}
    maze_map = {rid: maze_g[rid] for rid in TRAIN_IDS if rid in maze_g}

    merged = {"open": open_map, "maze": maze_map}

    with open(BEST_OUT, "w", encoding="utf-8") as f:
        json.dump(merged, f)
    with open(CURRENT_OUT, "w", encoding="utf-8") as f:
        json.dump(merged, f)

    print("Merged saved to", BEST_OUT, "and", CURRENT_OUT)

if __name__ == "__main__":
    main()
