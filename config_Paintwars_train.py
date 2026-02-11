# config_Paintwars_train_menad.py
# Entrainement (open/maze) avec arenas_menad (arenes 0..9)

import arenas_menad as arenas

import robot_menad
import robot_champion

# --- Paramètres généraux (peuvent être écrasés en ligne de commande) ---
display_mode = 2          # 0: temps réel, 1: rapide, 2: très rapide sans affichage
arena = 4                 # valeur par défaut (sera souvent écrasée par optimize_*.py)
position = False          # False: Challenger (A) à gauche, True: à droite
max_iterations = 500      # durée d'un match (peut être augmentée si besoin)

# --- Affichage / logs ---
display_welcome_message = False
verbose_minimal_progress = False
display_robot_stats = False
display_team_stats = False
display_tournament_results = True
display_time_stats = False

# --- Initialisation des robots ---
def initialize_robots(arena_size=-1, particle_box=-1):
    global position

    if position is False:
        x_init_pos = [4, 93]
        orientation_A = 0
        orientation_B = 180
    else:
        x_init_pos = [93, 4]
        orientation_A = 180
        orientation_B = 0

    robots = []

    # Team A (Menad) : menad_0..menad_3
    for i in range(4):
        robots.append(
            robot_menad.Robot_player(
                x_init_pos[0],
                arena_size // 2 - 16 + i * 8,
                orientation_A,
                name=f"menad_{i}",
                team="A",
            )
        )

    # Team B (Champion)
    for i in range(4):
        robots.append(
            robot_champion.Robot_player(
                x_init_pos[1],
                arena_size // 2 - 16 + i * 8,
                orientation_B,
                name="",
                team="B",
            )
        )

    return robots
