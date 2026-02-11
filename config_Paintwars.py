# Configuration file.

import arenas
import robot_menad
import robot_braitenberg_loveBot
import robot_wanderer
import WallFollowexr
import robot_braitenberg_hateWall
# general -- first three parameters can be overwritten with command-line arguments (cf. "python tetracomposibot.py --help")

display_mode = 0
arena = 4
position = False 
max_iterations = 1000 #401*500

# affichage
import arenas_menad as arenas

display_welcome_message = False
verbose_minimal_progress = False # display iterations
display_robot_stats = False
display_team_stats = False
display_tournament_results = True
display_time_stats = False

# initialization : create and place robots at initial positions (returns a list containing the robots)

import robot_challenger
import robot_champion
import robot_braitenberg_avoider
import robot_menad_final
import WallFollowexr
def initialize_robots(arena_size=-1, particle_box=-1): # particle_box: size of the robot enclosed in a square
    global position
    #x_center = arena_size // 2 - particle_box / 2
    #y_center = arena_size // 2 - particle_box / 2
    x_init_pos = []
    if position == False:
        x_init_pos = [4,93]
        orientation_champion = 0
        orientation_challenger = 180
    else:
        x_init_pos = [93,4]
        orientation_champion = 180
        orientation_challenger = 0
    robots = []
    robots.append(robot_menad.Robot_player(x_init_pos[0], arena_size//2-16+0*8, orientation_champion, name=f"menad_{0}", team="A"))
    robots.append(robot_menad.Robot_player(x_init_pos[0], arena_size//2-16+1*8, orientation_champion, name=f"menad_{1}", team="A"))

    robots.append(robot_menad.Robot_player(x_init_pos[0], arena_size//2-16+2*8, orientation_champion, name=f"menad_{2}", team="A"))
    robots.append(robot_menad.Robot_player(x_init_pos[0], arena_size//2-16+3*8, orientation_champion, name=f"menad_{3}", team="A"))

    robots.append(robot_champion.Robot_player(x_init_pos[1], arena_size//2-16+0*8, orientation_challenger, name="", team="B"))
    robots.append(robot_champion.Robot_player(x_init_pos[1], arena_size//2-16+1*8, orientation_challenger, name="", team="B"))
    robots.append(robot_champion.Robot_player(x_init_pos[1], arena_size//2-16+2*8, orientation_challenger, name="", team="B"))
    robots.append(robot_champion.Robot_player(x_init_pos[1], arena_size//2-16+3*8, orientation_challenger, name="", team="B"))
    return robots
