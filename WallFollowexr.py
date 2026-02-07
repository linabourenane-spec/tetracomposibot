from robot import *
import math

nb_robots = 0
debug = True

class Robot_player(Robot):

    team_name = "WallWalker" # Change le nom si tu veux
    robot_id = -1
    iteration = 0
    memory = 0 

    def __init__(self, x_0, y_0, theta_0, name="n/a", team="n/a"):
        global nb_robots
        self.robot_id = nb_robots
        nb_robots += 1
        super().__init__(x_0, y_0, theta_0, name=name, team=team)

    def step(self, sensors, sensor_view=None, sensor_robot=None, sensor_team=None):

        # 1. FILTRAGE : On ne veut voir que les MURS (on ignore les robots)
        sensor_to_wall = []
        for i in range(8):
            # Si c'est un mur (1) ou rien (0), on garde la distance.
            # Si c'est un robot (2), on considère que c'est loin (1.0) pour ne pas le "suivre"
            if sensor_view[i] == 2: 
                sensor_to_wall.append(1.0)
            else:
                sensor_to_wall.append(sensors[i])

        # 2. CHOIX DU CÔTÉ (Droit ou Gauche)
        # side = -1 pour DROITE (Robots 0, 2)
        # side =  1 pour GAUCHE (Robots 1, 3)
        side = -1 if (self.robot_id % 2 == 0) else 1
        
        # 3. SÉLECTION DES CAPTEURS
        # On récupère les valeurs des capteurs du bon côté
        if side == -1: # Suivre mur DROIT
            val_lat  = sensor_to_wall[4] # Capteur latéral (90°)
            val_diag = sensor_to_wall[3] # Capteur diagonal (45°)
        else:          # Suivre mur GAUCHE
            val_lat  = sensor_to_wall[0] # Capteur latéral (90°)
            val_diag = sensor_to_wall[1] # Capteur diagonal (45°)
            
        val_front = sensor_to_wall[2]    # Capteur devant

        # 4. LOGIQUE DE CONTRÔLE (Suiveur de Mur)
        translation = 1.0
        rotation = 0.0
        
        target_dist = 0.5 # Distance qu'on veut garder avec le mur

        # CAS A : Mur devant (Danger !) -> On tourne sec à l'opposé
        if val_front < 0.35:
            translation = 0.1 # On freine
            rotation = 0.8 * side * -1 # On tourne à l'opposé du mur
            
        # CAS B : On a perdu le mur latéral (Coin extérieur ou grand espace)
        elif val_lat > 0.8:
            # On avance en tournant doucement vers le côté qu'on suit pour le retrouver
            translation = 1.0
            rotation = 0.3 * side 
            
        # CAS C : On longe le mur (Régulation)
        else:
            translation = 0.8 # Vitesse de croisière
            
            # Calcul de l'erreur (Suis-je trop près ou trop loin ?)
            error = val_lat - target_dist
            
            # Correction Proportionnelle (P) : 
            # Si side Droite(-1) et trop près(error<0) -> On veut tourner Gauche(Rot>0)
            # Donc Rot = error * Gain * side * -1
            rotation = error * 1.5 * side * -1
            
            # Correction Dérivée (D) anticipée avec la diagonale :
            # Si le mur devant se rapproche (val_diag diminue), on commence à tourner
            rotation += (1.0 - val_diag) * 1.0 * side * -1

        self.iteration += 1        
        return translation, rotation, False