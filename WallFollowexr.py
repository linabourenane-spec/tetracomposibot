
from robot import * 
import math
nb_robots = 0
debug = True

class Robot_player(Robot):

    team_name = "Avoider"
    robot_id = -1
    iteration = 0

    def __init__(self, x_0, y_0, theta_0, name="n/a", team="n/a"):
        global nb_robots
        self.robot_id = nb_robots
        nb_robots+=1
        self.memory=0
        super().__init__(x_0, y_0, theta_0, name=name, team=team)
        self.genome=[
    # Première ligne : 10 valeurs
    0.732001, 1.000000, 0.288453, -0.641778, 1.000000, -0.307016, 0.373089, -1.000000, -1.000000, 0.178387,
    
    # Deuxième ligne : 10 valeurs  
    0.971844, -0.625796, 0.058872, -0.263537, 0.169514, 0.972480, -0.835509, 0.740569, 1.000000, 0.848189,
    
    # Troisième ligne : 10 valeurs
    0.577993, -0.172362, 0.083352, -0.347404, 0.118569, 0.209512, -1.000000, 0.116015, -0.041035, -0.607371,
    
    # Quatrième ligne : 10 valeurs
    0.094243, 0.136499, -0.592141, 0.622337, 0.619195, 0.317310, 0.435245, -0.867861, 0.940304, 0.957802,
    
    # Cinquième ligne : 10 valeurs
    0.643200, 0.317653, -0.422746, 0.421518, 1.000000, 0.022860, 0.718069, -0.451567, -0.774967, 0.966781,
    
    # Sixième ligne : 10 valeurs
    -0.156708, -0.806057, -0.457338, -0.033177, 0.513030, 0.713167, -0.947412, 1.000000, 0.883274, 1.000000,
    
    # Septième ligne : 10 valeurs
    -0.155723, -0.365881, -0.024925, -0.859962, -0.663725, -0.876597, -0.420827, 0.794838, 0.337912, 0.512835,
    
    # Huitième ligne : 10 valeurs
    -0.207010, -0.037749, -0.290094, 0.268448, -0.112666, 0.003713, 0.928395, 1.000000, 1.000000, 0.233610,
    
    # Neuvième ligne : 10 valeurs
    0.857724, 0.305542, -0.925630, 1.000000, -1.000000, -0.352709, 0.032581, 1.000000, -0.335217, 0.029052,
    
    # Dixième ligne : 10 valeurs
    0.267355, 0.433039, -1.000000, 1.000000, -1.000000, 0.311511, 0.367553, 1.000000, -0.818103, -0.022640,
    
    # Onzième ligne : 10 valeurs
    -0.880840, 1.000000, 0.967335, 0.644427, 0.360866, -0.236028, -0.671877, -0.869968, 0.511099, -0.220600,
    
    # Douzième ligne : 10 valeurs
    0.986906, -0.462850, -0.716963, 0.652843, -0.220429, 1.000000, -1.000000, -0.941159, 1.000000, 0.834655,
    
    # Treizième ligne : 10 valeurs
    -1.000000, -1.000000, 0.278768, -0.450555, -0.984895, 0.631699, 0.213262, -0.771252, 1.000000, -0.931059,
    
    # Quatorzième ligne : 10 valeurs
    -1.000000, 0.163322, -0.624799, -0.203664, -0.098393, -0.417024, 1.000000, -1.000000, -0.591779, -0.066274,
    
    # Quinzième ligne : 2 valeurs (les 2 dernières)
    1.000000, -0.445124
]



    def step(self, sensors, sensor_view=None, sensor_robot=None, sensor_team=None):

        sensor_to_wall = []
        sensor_to_robot = []
        for i in range (0,8):
            if  sensor_view[i] == 1:
                sensor_to_wall.append( sensors[i] )
                sensor_to_robot.append(1.0)
            elif  sensor_view[i] == 2:
                sensor_to_wall.append( 1.0 )
                sensor_to_robot.append( sensors[i] )
            else:
                sensor_to_wall.append(1.0)
                sensor_to_robot.append(1.0)

        if debug == True:
            if self.iteration % 100 == 0:
                print ("Robot",self.robot_id," (team "+str(self.team_name)+")","at step",self.iteration,":")
                print ("\tsensors (distance, max is 1.0)  =",sensors)
                print ("\t\tsensors to wall  =",sensor_to_wall)
                print ("\t\tsensors to robot =",sensor_to_robot)
                print ("\ttype (0:empty, 1:wall, 2:robot) =",sensor_view)
                print ("\trobot's name (if relevant)      =",sensor_robot)
                print ("\trobot's team (if relevant)      =",sensor_team)

        if self.id%2==0:
            if sensor_to_wall[sensor_front] < 0.2 or sensor_to_wall[sensor_front_left] < 0.2 or sensor_to_wall[sensor_front_right] < 0.2:
    
                translation =1.0
            
                rotation =  (sensors[sensor_rear_left]-sensor_to_wall[sensor_front_left])*(-1)+(sensors[sensor_rear_left]-sensor_to_wall[sensor_front_right])+(sensors[sensor_rear_left]-sensor_to_wall[sensor_front])+(sensors[sensor_rear_left]-sensor_to_wall[sensor_left])*(-1)+(sensors[sensor_rear_left]-sensor_to_wall[sensor_right])


            else:
                if self.memory%15!=0 :
                    translation = 1.0
            
                    rotation =  (sensors[sensor_rear_left]-sensor_to_wall[sensor_front_left])+(sensors[sensor_rear_left]-sensor_to_wall[sensor_front_right])*(-1)+(sensors[sensor_rear_left]-sensor_to_wall[sensor_front])*(-1)
                else:
        
            
                    translation,rotation =  self.neural_network( sensors, sensor_view, sensor_team)

            self.memory+=1
            self.iteration = self.iteration + 1  
        else : 
                    translation = sensors[sensor_front] # A MODIFIER
                    rotation = (sensors[sensor_rear_left]-sensors[sensor_front_left])*(-1)+(sensors[sensor_rear_left]-sensors[sensor_front_right])+(sensors[sensor_rear_left]-sensors[sensor_front])

        return translation, rotation, False
        


    def neural_network(self, sensors, sensor_view, sensor_team):
        """Passe avant du réseau de neurones avec le génome pré-entraîné"""
        # --- A. Préparation des Entrées (25 inputs) ---
        inputs = []
        # 8 distances
        inputs.extend(sensors)
        # 8 murs (1.0 si mur, 0.0 sinon)
        inputs.extend([1.0 if v == 1 else 0.0 for v in sensor_view])
        # 8 ennemis (1.0 si ennemi, 0.0 sinon)
        inputs.extend([1.0 if (t != "n/a" and t != self.team) else 0.0 for t in sensor_team])
        # 1 mémoire (normalisée entre -1 et 1)
        inputs.append(self.memory / 100.0 if self.memory != 0 else 0.0)

        # --- B. Couche Cachée (Hidden Layer) ---
        hidden_outputs = []
        nb_hidden = 5
        idx = 0

        for h in range(nb_hidden):
            activation = 0
            # Poids des entrées
            for inp in inputs:
                activation += inp * self.genome[idx]
                idx += 1
            # Biais
            activation += self.genome[idx]
            idx += 1
            # Fonction d'activation
            hidden_outputs.append(math.tanh(activation))

        # --- C. Couche de Sortie (Output Layer) ---
        outputs = []
        nb_outputs = 2

        for o in range(nb_outputs):
            activation = 0
            # Poids venant de la couche cachée
            for h_out in hidden_outputs:
                activation += h_out * self.genome[idx]
                idx += 1
            # Biais
            activation += self.genome[idx]
            idx += 1
            # Fonction d'activation
            outputs.append(math.tanh(activation))

        return outputs[0], outputs[1]  # translation, rotation
