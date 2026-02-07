from robot import *
import math

nb_robots = 0
debug = True  # Mettre à False pour le tournoi pour gagner un peu de perf

class Robot_player(Robot):

    # Donne un nom à ton équipe ici
    team_name = "L'Agence Tous Risques"
    
    # Identifiants et mémoire
    robot_id = -1
    iteration = 0
    memory = 0 # L'unique entier autorisé pour la logique

    def __init__(self, x_0, y_0, theta_0, name="n/a", team="n/a"):
        global nb_robots
        self.robot_id = nb_robots
        nb_robots += 1
        super().__init__(x_0, y_0, theta_0, name=name, team=team)

    def step(self, sensors, sensor_view=None, sensor_robot=None, sensor_team=None):

        # 1. TRI DES CAPTEURS (Code fourni)
        # On sépare ce qui est un mur de ce qui est un robot
        sensor_to_wall = []
        sensor_to_robot = []
        for i in range(0, 8):
            if sensor_view[i] == 1: # C'est un MUR
                sensor_to_wall.append(sensors[i])
                sensor_to_robot.append(1.0) # On ignore (distance max)
            elif sensor_view[i] == 2: # C'est un ROBOT
                sensor_to_wall.append(1.0) # On ignore (distance max)
                sensor_to_robot.append(sensors[i])
            else: # RIEN
                sensor_to_wall.append(1.0)
                sensor_to_robot.append(1.0)

        # ----------------------------------------------------------------------
        # 2. GESTION DE LA MÉMOIRE (State Machine)
        # ----------------------------------------------------------------------
        # self.memory est notre "cerveau" temporel.
        # 0       : Initialisation
        # 1 - 40  : Phase de DISPERSION (Début de match)
        # 100     : Comportement Normal (Strikers ou Wall Followers)
        # > 200   : Mode URGENCE (Déblocage)
        
        if self.memory == 0: 
            self.memory = 1
        
        trans = 0
        rot = 0
        
        # ----------------------------------------------------------------------
        # 3. PHASE DE DISPERSION (0 à 4 secondes environ)
        # ----------------------------------------------------------------------
        if self.memory < 40:
            self.memory += 1
            # Chaque robot part dans une direction différente pour ne pas se gêner
            speed = 1.0
            if self.robot_id == 0: return speed, 0.5, False   # Courbe Gauche
            if self.robot_id == 1: return speed, -0.5, False  # Courbe Droite
            if self.robot_id == 2: return speed, 0.0, False   # Tout droit
            if self.robot_id == 3: return -1.0, 1.0, False    # Recule et tourne
            
        # Transition vers le mode normal
        elif self.memory == 40:
            self.memory = 100

        # ----------------------------------------------------------------------
        # 4. MODE URGENCE (WATCHDOG)
        # ----------------------------------------------------------------------
        # Si le compteur est supérieur à 200, c'est qu'on est en train de se débloquer
        if self.memory > 200:
            self.memory -= 1
            # Si on a fini le déblocage, on remet à 100
            if self.memory == 200: self.memory = 100
            # Action de déblocage : Reculer et tourner fort
            return -0.3, 1.0, False

        # DÉTECTION DE BLOCAGE
        # Si on est en mode normal (100) et qu'on est collé au mur devant (< 0.2)
        if self.memory == 100 and sensors[sensor_front] < 0.2:
            self.memory = 220 # On active le mode urgence pour 20 tours
            return 0, 0, False

        # ----------------------------------------------------------------------
        # 5. STRATÉGIE PAR TYPE DE ROBOT
        # ----------------------------------------------------------------------
        
        # === ÉQUIPE A : LES STRIKERS (Robots 0 et 1) ===
        # Objectif : Vitesse max, rebonds fluides (Arènes 0, 1)
        if self.robot_id == 0 or self.robot_id == 1:
            
            # --- POIDS GÉNÉTIQUES (Place ici tes meilleurs poids trouvés !) ---
            # Exemple de poids "agressifs"
            w_trans = [0.1, 0.1, -2.0, 0.1, 0.1, 0, 0, 0] # Le capteur frontal (-2.0) freine fort
            w_rot   = [-0.8, -0.6, 0.0, 0.6, 0.8, 0, 0, 0] # Tourne à l'opposé des murs
            
            # Calcul Braitenberg
            sum_t = 1.0 # Biais avance (envie d'avancer par défaut)
            sum_r = 0.0
            
            # On utilise 'sensors' (on évite tout : murs et robots)
            for i in range(5): # On regarde les 5 capteurs avant
                sum_t += sensors[i] * w_trans[i]
                sum_r += sensors[i] * w_rot[i]
                
            trans = math.tanh(sum_t)
            rot = math.tanh(sum_r)

        # === ÉQUIPE B : LES WALL FOLLOWERS (Robots 2 et 3) ===
        # Objectif : Labyrinthes, Rayures, Séparation (Arènes 2, 3, 4)
        else:
            # Robot 2 suit MUR DROIT (-1), Robot 3 suit MUR GAUCHE (1)
            side = -1 if self.robot_id == 2 else 1
            
            # Sélection des capteurs selon le côté (Mur ou Robot ? On suit les MURS)
            # On utilise sensor_to_wall pour ne pas essayer de "longer" un robot ennemi
            if side == -1: # Droite
                s_lat = sensor_to_wall[4] # Droite 90°
                s_diag = sensor_to_wall[3] # Droite 45°
            else: # Gauche
                s_lat = sensor_to_wall[0] # Gauche 90°
                s_diag = sensor_to_wall[1] # Gauche 45°
            
            s_front = sensor_to_wall[2] # Devant
            
            target = 0.5 # Distance idéale au mur
            
            # Logique PID manuelle
            if s_front < 0.35: # Mur devant -> Virage sec
                trans = 0.1
                rot = 1.0 * side * -1 # Opposé au côté
            elif s_lat > 0.8: # Perdu le mur -> On le cherche doucement
                trans = 1.0
                rot = 0.3 * side 
            else: # On longe -> Régulation
                error = s_lat - target
                # Formule : Correction prop + Anticipation (diag)
                rot = (error * 1.5 * side * -1) + ((1.0 - s_diag) * 0.8 * side * -1)
                trans = 0.8 # Vitesse contrôlée

        # Mise à jour compteur global (pour debug seulement)
        self.iteration += 1        
        
        return trans, rot, False