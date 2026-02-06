# Nicolas
# 2025-03-24
#
# comportement par défaut
#

from robot import *

nb_robots = 0
debug = False


class Robot_player(Robot):
    team_name = "Professor X"
    robot_id = -1
    iteration = 0

    def __init__(self, x_0, y_0, theta_0, name="n/a", team="n/a"):
        global nb_robots
        self.robot_id = nb_robots
        nb_robots += 1
        super().__init__(x_0, y_0, theta_0, name="Robot " + str(self.robot_id), team=self.team_name)

    def step(self, sensors, sensor_view=None, sensor_robot=None, sensor_team=None):
        translation = sensors[sensor_front] * 0.1 + 0.2
        rotation = 0.2 * sensors[sensor_left] + 0.2 * sensors[sensor_front_left] - 0.2 * sensors[sensor_right] - 0.2 * \
                   sensors[sensor_front_right] + (random.random() - 0.5) * 1.  # + sensors[sensor_front] * 0.1
        if debug == True:
            if self.iteration % 100 == 0 and self.robot_id == 0:
                print("Robot", self.robot_id, "(team " + str(self.team_name) + ")", "at step", self.iteration, ":")
                print("\tsensors (distance, max is 1.0)  =", sensors)
                print("\ttype (0:empty, 1:wall, 2:robot) =", sensor_view)
                print("\trobot's name (if relevant)      =", sensor_robot)
                print("\trobot's team (if relevant)      =", sensor_team)
        self.iteration = self.iteration + 1
        return translation, rotation, False


'''
def step(robotId, sensors):

    translation = 1
    rotation = 0
    if sensors["sensor_front_left"]["distance"] < 1 or sensors["sensor_front"]["distance"] < 1:
        rotation = 0.5
    elif sensors["sensor_front_right"]["distance"] < 1:
        rotation = -0.5

    return translation, rotation, False
'''









# Projet "robotique" IA&Jeux 2025
#
# Binome:
#  Prénom Nom No_étudiant/e : _________
#  Prénom Nom No_étudiant/e : _________
#
# check robot.py for sensor naming convention
# all sensor and motor value are normalized (from 0.0 to 1.0 for sensors, -1.0 to +1.0 for motors)

from robot import *

nb_robots = 0

class Robot_player(Robot):

    team_name = "Challenger"  # vous pouvez modifier le nom de votre équipe
    robot_id = -1             # ne pas modifier. Permet de connaitre le numéro de votre robot.
    memory = 0                # vous n'avez le droit qu'a une case mémoire qui doit être obligatoirement un entier

    def __init__(self, x_0, y_0, theta_0, name="n/a", team="n/a"):
        global nb_robots
        self.robot_id = nb_robots
        nb_robots+=1
        super().__init__(x_0, y_0, theta_0, name="Robot "+str(self.robot_id), team=self.team_name)

    def step(self,robotId, sensors, sensor_view=None, sensor_robot=None, sensor_team=None):

        translation = sensors[sensor_front]
        rotation = 1.0 * sensors[sensor_front_left] - 1.0 * sensors[sensor_front_right] + (random.random()-0.5)*0.1
        return translation, rotation, False


