# Projet "robotique" IA&Jeux 2025
#
# Binome:
#  Prénom Nom No_étudiant/e : Amel BEN CHABANE 21304456
#  Prénom Nom No_étudiant/e : Tassadit AKSAS 21302943
#
# check robot.py for sensor naming convention
# all sensor and motor value are normalized (from 0.0 to 1.0 for sensors, -1.0 to +1.0 for motors)

from robot import * 
import random
#import robot_ga 
import math
nb_robots = 0

class Robot_player(Robot):

    """
    Challenger arbre de comportement:
    1. Eviter les ennemis (si un robot ennemi est détecté, tourner dans l'autre direction).
    2. Longer un mur si il est latéral avec une probabilité de 0.9, sinon éviter.
    3. Eviter les murs.
    4. Utiliser un comportement optimisé par un agent génétique.
    """

    team_name = "A"  # vous pouvez modifier le nom de votre équipe
    robot_id = -1             # ne pas modifier. Permet de connaitre le numéro de votre robot.
    memory = 0                # vous n'avez le droit qu'a une case mémoire qui doit être obligatoirement un entier

    LATERAL_SENSORS = [sensor_front_left, sensor_left, sensor_front_right, sensor_right]
    NON_LATERAL_SENSORS = [sensor_front, sensor_rear_left, sensor_rear, sensor_rear_right]

    def __init__(self, x_0, y_0, theta_0, name="n/a", team="n/a"):
        global nb_robots
        self.robot_id = nb_robots
        nb_robots+=1
       # self.ga_agent = robot_ga.Robot_player(x_0, y_0, theta_0, name=team, team=self.team_name)
        super().__init__(x_0, y_0, theta_0, name="Robot "+str(self.robot_id), team=self.team_name)
        self.param = [1,0,1,1,1,1,-1,-1]


    def reset(self):
        super().reset()
       # self.ga_agent.reset()

    def step(self, sensors, sensor_view=None, sensor_robot=None, sensor_team=None):
         # 1) detection d'un robot ennemi = tourner dans l'autre direction
        if any(view == 2 for view in sensor_view):  # Si un robot ennemi est détecté
            return 1.0, 1.0, False  # Avancer et tourner dans l'autre direction

        # 2) detection d'un mur lateral
        if sensor_view and any(sensor_view[i] == 1 for i in self.LATERAL_SENSORS):
            if random.random() < 0.9:  # Suivre le mur avec une probabilité de 0.9
                thr = sensors[sensor_front]  # Distance à l'obstacle devant
                translation = thr * 0.5  # Avancer
                rot_left = sensors[sensor_left] + sensors[sensor_front_left]
                rot_right = sensors[sensor_right] + sensors[sensor_front_right]
                rotation = (rot_left - rot_right) * 0.2  # Rotation pour suivre le mur
                rotation = max(min(rotation, 1.0), -1.0)  # Limite la rotation entre -1 et 1
                return translation, rotation, False
            else:  # Sinon, éviter le mur
                free_dirs = [i for i in range(8) if not (sensor_view and sensor_view[i] == 1)]
                if not free_dirs:
                    return 1.0, random.uniform(-1.0, 1.0), False
                dir_idx = random.choice(free_dirs)
                angle = dir_idx * 45 if dir_idx <= 4 else (dir_idx - 8) * 45
                if angle > 180:
                    angle -= 360
                rotation = angle / 180.0
                return 1.0, rotation, False

        # 3) Détection d un mur non-lateral
        if sensor_view and any(sensor_view[i] == 1 for i in self.NON_LATERAL_SENSORS):
            free_dirs = [i for i in range(8) if not (sensor_view and sensor_view[i] == 1)]
            if not free_dirs:
                return 1.0, random.uniform(-1.0, 1.0), False
            dir_idx = random.choice(free_dirs)
            angle = dir_idx * 45 if dir_idx <= 4 else (dir_idx - 8) * 45
            if angle > 180:
                angle -= 360
            rotation = angle / 180.0
            return 1.0, rotation, False

        # 4) Sinon : comportement optimise par l agent génétique
        t = math.tanh(
            self.param[0]
            + self.param[1] * sensors[sensor_front_left]
            + self.param[2] * sensors[sensor_front]
            + self.param[3] * sensors[sensor_front_right]
        )
        r = math.tanh(
            self.param[4]
            + self.param[5] * sensors[sensor_front_left]
            + self.param[6] * sensors[sensor_front]
            + self.param[7] * sensors[sensor_front_right]
        )
        return t, r, False
        #return self.ga_agent.step(sensors, sensor_view, sensor_robot, sensor_team)

