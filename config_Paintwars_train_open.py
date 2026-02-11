# config_Paintwars_train_open.py

import arenas_menad as arenas
import robot_menad
import robot_champion

display_mode = 2
arena = 1
position = False
max_iterations = 500

display_welcome_message = False
verbose_minimal_progress = False
display_robot_stats = False
display_team_stats = False
display_tournament_results = True
display_time_stats = False

def initialize_robots(arena_size=-1, particle_box=-1):
    global position

    if position == False:
        x_init_pos = [4, 93]
        orientation_A = 0
        orientation_B = 180
    else:
        x_init_pos = [93, 4]
        orientation_A = 180
        orientation_B = 0

    robots = []
    for i in range(4):
        robots.append(robot_menad.Robot_player(
            x_init_pos[0],
            arena_size//2 - 16 + i*8,
            orientation_A,
            name=f"menad_{i}",
            team="A"
        ))
    for i in range(4):
        robots.append(robot_champion.Robot_player(
            x_init_pos[1],
            arena_size//2 - 16 + i*8,
            orientation_B,
            name=f"champ_{i}",
            team="B"
        ))
    return robots
