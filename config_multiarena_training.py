# Configuration file for multi-arena training
# Ce fichier simule le changement d'arène en réinitialisant avec une nouvelle arène

import arenas
import robot_multiarena_trainer_v2 as robot_trainer

# Paramètres généraux
display_mode = 1  # Mode rapide sans affichage
arena = 0  # Arène initiale - sera écrasé par ligne de commande
position = False

# Affichage
display_welcome_message = False  # Désactivé pour moins de bruit
verbose_minimal_progress = False
display_robot_stats = False
display_team_stats = False
display_tournament_results = False
display_time_stats = False  # Désactivé pendant l'entraînement

# Paramètres d'optimisation
evaluations = 200  # Évaluations par arène (pas total)
it_per_evaluation = 400  # Steps par évaluation
max_iterations = evaluations * it_per_evaluation * 2  # Large marge

# Position initiale SAFE pour toutes les arènes
SAFE_START_X = 50  # Centre de l'arène (100x100)
SAFE_START_Y = 50
SAFE_START_THETA = 0


def initialize_robots(arena_size=-1, particle_box=-1):
    x_center = arena_size // 2 - particle_box / 2
    y_center = arena_size // 2 - particle_box / 2

    robots = []

    # Position sécurisée loin des murs
    start_x = SAFE_START_X
    start_y = SAFE_START_Y
    start_theta = SAFE_START_THETA

    # Ajuster selon l'arène
    if arena == 1:  # Arène avec obstacles centraux
        start_x = 20
        start_y = 20
    elif arena == 2:  # Arène avec lignes
        start_x = 25
        start_y = 25
    elif arena == 3:  # Arène verticale
        start_x = 30
        start_y = 30
    elif arena == 4:  # Labyrinthe
        start_x = 10
        start_y = 10
        start_theta = 90

    print(f"Initializing robot at position: ({start_x}, {start_y}), theta: {start_theta}")

    # Créer le robot d'entraînement
    robot = robot_trainer.Robot_player(
        start_x, start_y, start_theta,
        name=f"Trainer-Arena{arena}",
        team="Trainer",
        evaluations=evaluations,
        it_per_evaluation=it_per_evaluation
    )

    robots.append(robot)

    return robots