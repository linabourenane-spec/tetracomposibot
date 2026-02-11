# Projet "robotique" IA&Jeux 2025
#
# Binome:
#  Prénom Nom: LIM Oudam-dara
#  Prénom Nom: GU David
#
# check robot.py for sensor naming convention
# all sensor and motor value are normalized (from 0.0 to 1.0 for sensors, -1.0 to +1.0 for motors)

from robot import * 
import math
nb_robots = 0

class Robot_player(Robot):

    team_name = "A"  # vous pouvez modifier le nom de votre équipe
    robot_id = -1             # ne pas modifier. Permet de connaitre le numéro de votre robot.
    memory = 0                # vous n'avez le droit qu'a une case mémoire qui doit être obligatoirement un entier

    def __init__(self, x_0, y_0, theta_0, name="n/a", team="n/a"):
        global nb_robots
        self.robot_id = nb_robots
        nb_robots+=1
        super().__init__(x_0, y_0, theta_0, name=name, team=self.team_name)

    def step(self, sensors, sensor_view=None, sensor_robot=None, sensor_team=None):
        sensor_to_wall = []
        sensor_to_robot = []
        sensor_to_ally = []
        for i in range (0,8):
            if  sensor_view[i] == 1:
                sensor_to_wall.append( sensors[i] )
                sensor_to_robot.append(1.0)
                sensor_to_ally.append(1.0)
            elif  sensor_view[i] == 2:
                sensor_to_wall.append( 1.0 )
                if sensor_team[i] != self.team_name:
                    sensor_to_robot.append( sensors[i] )
                    sensor_to_ally.append(1.0)
                else : 
                    sensor_to_ally.append(sensors[i])
                    sensor_to_robot.append(1.0)
            else:
                sensor_to_wall.append(1.0)
                sensor_to_robot.append(1.0)
                sensor_to_ally.append(1.0)


        STUCK_THRESHOLD = 30
        STUCK_THRESHOLD2 = 60
        WALL_TH = 0.65 

        blocked_front = sensors[sensor_front] < WALL_TH
        blocked_front_left = sensors[sensor_front_left] < WALL_TH
        blocked_front_right = sensors[sensor_front_right] < WALL_TH
        blocked_left = sensors[sensor_left] < WALL_TH
        blocked_right = sensors[sensor_right] < WALL_TH

        is_followed = sensor_to_robot[sensor_rear] !=1 or sensor_to_robot[sensor_rear_left] != 1 or sensor_to_robot[sensor_rear_right] != 1
        is_stuck =  (blocked_front and (blocked_left or blocked_front_left)) or ((blocked_front_right or blocked_right) and blocked_front)
        is_chasing = sensor_to_robot[sensor_front] != 1 or sensor_to_robot[sensor_front_right] != 1 or sensor_to_robot[sensor_front_left] != 1
        

        if is_stuck and not is_chasing:
            self.memory += 1
        else:
            self.memory = 0 

        #Il est bloqué pendant x temps (défini par STUCK_THRESHOLD)
        if self.memory > STUCK_THRESHOLD:
            #print(f"Je suis le robot {self.robot_id} et je suis bloqué")
            translation = -0.05
            rotation    = 0.4
            #Si il est bloqué pendant y temps, il va alors se tourner de manière plus précise
            if self.memory > STUCK_THRESHOLD2:
                translation = -0.05
                rotation    = 0.1
            
            return translation, rotation, False
        
        """ #Bloque dans un labyrinthe dans un coin cocave.
        if self.robot_id == 1 :
            #Evite le coin
            if sensors[sensor_front] < WALL_TH:
                translation = -0.2
                rotation = 1
                return translation, rotation, False

            #Longe le mur à gauche
            if sensor_to_wall[sensor_left] < WALL_TH or sensor_to_wall[sensor_front_left] < WALL_TH:
                translation = 0.5 * sensor_to_wall[sensor_front]
                if sensor_to_wall[sensor_left] < 0.39:
                    rotation = 1 * sensor_to_wall[sensor_front_left] - 1 * sensor_to_wall[sensor_front_right] + 1*sensor_to_wall[sensor_front] -1*sensor_to_wall[sensor_rear]
                else:
                    rotation =  0.1 
                return translation, rotation, False
            
            #Longe le mur à droite
            if sensor_to_wall[sensor_right] < WALL_TH or sensor_to_wall[sensor_front_right] < WALL_TH:
                translation = 0.5 * sensor_to_wall[sensor_front]
                if sensor_to_wall[sensor_right] < 0.39 :
                    rotation = 1 * sensor_to_wall[sensor_front_left] - 1 * sensor_to_wall[sensor_front_right] + 1*sensor_to_wall[sensor_front] -1*sensor_to_wall[sensor_rear]
                else:
                    rotation =  -0.1
                return translation, rotation, False

            translation = 0.8*sensor_to_wall[sensor_front]
            rotation = 0

            return translation, rotation, False
        """
        
        #S'il est bloqué
        if (blocked_front and blocked_front_left) or (blocked_front and blocked_front_right): 
            translation = sensors[sensor_front]*0.3
            rotation = 0.6 * sensors[sensor_front_left] - 0.6 * sensors[sensor_front_right] + 0.6* sensors[sensor_left] - 0.6 * sensors[sensor_right] 
            #print ("\tsensors (distance, max is 1.0)  =",sensors)
            return translation, rotation, False
        
        #Evite le robot allié   
        if sensor_to_ally[sensor_front_left] != 1 or sensor_to_ally[sensor_front_right] != 1 or sensor_to_ally[sensor_front] != 1 :
            translation = sensors[sensor_front]*0.7
            rotation = 1 * sensor_to_ally[sensor_front_left] - 1 * sensor_to_ally[sensor_front_right] + (1-sensor_to_ally[sensor_front])
            return translation, rotation, False

        #Suis un robot ennemi
        if is_chasing :
            translation = sensors[sensor_front]*0.8
            rotation = 1.0 *sensor_to_robot[sensor_front_right] -1.0 * sensor_to_robot[sensor_front_left]
            return translation, rotation, False
        
        #S'il est suivis, attends sur place et se retourne
        if is_followed :
            translation = 0.05
            rotation = 1.0*sensor_to_robot[sensor_rear_right] - 1.0*sensor_to_robot[sensor_rear_left] + (1-sensor_to_robot[sensor_rear])
            return translation, rotation, False
        

        
        #Par défaut        
        #print ("\tsensors (distance, max is 1.0)  =",sensors)
        translation = sensors[sensor_front]*0.8 - (1-sensor_rear)
        rotation = 0.2 * sensors[sensor_left] + 0.2 * sensors[sensor_front_left] - 0.2 * sensors[sensor_right] - 0.2 * sensors[sensor_front_right] + (random.random()-0.5)*1

        return translation, rotation, False
