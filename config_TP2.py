# Configuration file.

import arenas
import robot_challenger_training


# general -- first three parameters can be overwritten with command-line arguments (cf. "python tetracomposibot.py --help")

display_mode = 1
arena = 1
position = False 

# affichage

display_welcome_message = False
verbose_minimal_progress = False # display iterations
display_robot_stats = False
display_team_stats = False
display_tournament_results = False
display_time_stats = True

# optimization

evaluations = 600
it_per_evaluation = 500
max_iterations = 1000000

# initialization : create and place robots at initial positions (returns a list containing the robots)

import randomsearch2
import genetic_algorithms
import WallFollowexr

def initialize_robots(arena_size=-1, particle_box=-1): # particle_box: size of the robot enclosed in a square
    x_center = 5
    y_center = arena_size // 5 - particle_box / 2
    robots = []

    robots.append(WallFollowexr.Robot_player(25, y_center, 0, name="First Robot", team="Team Wander"))


    return robots

