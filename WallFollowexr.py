# robot_challenger.py - VERSION CORRECTE

from robot import *

team_name = "PureBraitenberg"

class Robot_player(Robot):
    memory = 0
    
    def __init__(self, x_0, y_0, theta_0, name="n/a", team="n/a"):
        super().__init__(x_0, y_0, theta_0, name, team)
        self.behavior_type = 0  # Simplifié
    
    def step(self, sensors, sensor_view=None, sensor_robot=None, sensor_team=None):

        
        # PAR DÉFAUT : avance tout droit
        translation = 0.6  # Avance à 60% vitesse
        rotation = 0.0     # Pas de rotation
        
        # -------------------------------------------------
        # 1. ÉVITER LES OBSTACLES (comme coward_behavior)
        # -------------------------------------------------
        # Inverser les distances
        sensor_values = [1.0 - d for d in sensors]
        
        # Calculer l'effet des obstacles
        obstacle_effect = 0.0
        
        for i in range(8):
            if sensor_view and sensor_view[i] in [1, 2]:  # Mur ou robot
                if i in [0, 1, 2, 7]:  # Obstacle à GAUCHE
                    # Tourne à DROITE pour fuir
                    rotation += sensor_values[i] * 0.5
                elif i in [4, 5, 6]:  # Obstacle à DROITE
                    # Tourne à GAUCHE pour fuir
                    rotation -= sensor_values[i] * 0.5
                elif i == 3:  # Obstacle DEVANT
                    # Reculer un peu et tourner
                    translation = -0.3
                    rotation = 0.5  # Tourne à droite
        
        # -------------------------------------------------
        # 2. CHERCHER LES ZONES ENNEMIES (comme zone_seeker)
        # -------------------------------------------------
        if sensor_team is not None:
            red_left = 0
            red_right = 0
            red_front = 0
            
            for i in range(8):
                if sensor_team[i] != "n/a" and sensor_team[i] != self.team:
                    if i in [0, 1, 2, 7]:
                        red_left += 1
                    elif i in [4, 5, 6]:
                        red_right += 1
                    elif i == 3:
                        red_front += 1
            
            # Plus de rouge à droite → tourne à droite
            if red_right > red_left:
                rotation -= (red_right - red_left) * 0.3
            
            # Plus de rouge à gauche → tourne à gauche
            elif red_left > red_right:
                rotation += (red_left - red_right) * 0.3
            
            # Rouge juste devant → ACCÉLÈRE !
            if red_front > 0:
                translation = 0.9  # Avance vite !
        
        # -------------------------------------------------
        # 3. LIMITES
        # -------------------------------------------------
        translation = max(-1.0, min(1.0, translation))
        rotation = max(-1.0, min(1.0, rotation))
        
        return translation, rotation, False