# robot_braitenberg_simple.py

from robot import *
import math

team_name = "PureBraitenberg"


# Définition des capteurs (8 au total)
sensor_back_left = 0
sensor_left = 1
sensor_front_left = 2
sensor_front = 3
sensor_front_right = 4
sensor_right = 5
sensor_back_right = 6
sensor_back = 7

class Robot_player(Robot):
    robot_id = -1
    memory = 0
    
    def __init__(self, x_0, y_0, theta_0, name="n/a", team="n/a"):
        super().__init__(x_0, y_0, theta_0, name, team)
        # Braitenberg pur : chaque robot a un comportement fixe selon son ID
        self.behavior_type = self.robot_id % 4  # 4 types de comportements
        
    def step(self, sensors, sensor_view=None, sensor_robot=None, sensor_team=None):
        """
        Braitenberg pur avec poids -1, 0, 1 seulement.
        """
        
        # 1. COMPORTEMENTS BRAITENBERG PURS
        if self.behavior_type == 0:
            # Type 1: Éviteur de murs (coward)
            return self.coward_behavior(sensors, sensor_view)
        
        elif self.behavior_type == 1:
            # Type 2: Suiveur de murs (wall follower)
            return self.wall_follower_behavior(sensors, sensor_view)
        
        elif self.behavior_type == 2:
            # Type 3: Chercheur de zones (zone seeker)
            return self.zone_seeker_behavior(sensors, sensor_team)
        
        else:  # behavior_type == 3
            # Type 4: Agressif (attacker)
            return self.aggressive_behavior(sensors, sensor_view, sensor_team)
    
    # ============================================
    # COMPORTEMENT 1: ÉVITEUR (COWARD)
    # ============================================
    def coward_behavior(self, sensors, sensor_view):
        """
        Braitenberg Type 1a: Coward (fuyard)
        Les objets proches font reculer les roues correspondantes.
        Poids: -1 pour les capteurs correspondants à leur roue.
        """
        # Poids purs -1, 0, 1
        # Gauche: influence négative si obstacle à gauche
        # Droite: influence négative si obstacle à droite
        
        base_speed = 0.7
        left_speed = base_speed
        right_speed = base_speed
        
        # Inverser les distances (1.0 = proche, 0.0 = loin)
        sensor_values = [1.0 - d for d in sensors]
        
        # Matrice de poids BRAITENBERG PUR (-1, 0, 1)
        # Capteurs: BL, L, FL, F, FR, R, BR, B
        weights_left =  [-1, -1, -1,  0,  0,  0,  0,  0]  # Les obstacles gauche ralentissent roue gauche
        weights_right = [ 0,  0,  0,  0, -1, -1, -1,  0]  # Les obstacles droit ralentissent roue droite
        
        for i in range(8):
            if sensor_view and sensor_view[i] in [1, 2]:  # Mur ou robot
                influence = sensor_values[i]
                left_speed += weights_left[i] * influence
                right_speed += weights_right[i] * influence
        
        # Normaliser
        left_speed = max(-1.0, min(1.0, left_speed))
        right_speed = max(-1.0, min(1.0, right_speed))
        
        return left_speed, right_speed, False
    
    # ============================================
    # COMPORTEMENT 2: SUIVEUR DE MUR (WALL FOLLOWER)
    # ============================================
    def wall_follower_behavior(self, sensors, sensor_view):
        """
        Braitenberg pour suivre un mur à droite.
        Poids: attraction/repulsion simple.
        """
        base_speed = 0.6
        left_speed = base_speed
        right_speed = base_speed
        
        sensor_values = [1.0 - d for d in sensors]
        
        # Poids pour suivre mur à DROITE
        # Si mur à droite: gauche accélère, droite ralentit
        weights_left =  [ 0,  0,  0,  0,  0,  1,  0,  0]  # Mur droit accélère gauche
        weights_right = [ 0,  0,  0,  0,  0, -1,  0,  0]  # Mur droit ralentit droite
        
        # Poids pour éviter mur devant
        weights_left += [0, 0, 0, -1, 0, 0, 0, 0]  # Devant ralentit gauche
        weights_right += [0, 0, 0, -1, 0, 0, 0, 0] # Devant ralentit droite aussi
        
        for i in range(8):
            if sensor_view and sensor_view[i] == 1:  # Mur seulement
                influence = sensor_values[i]
                left_speed += weights_left[i] * influence
                right_speed += weights_right[i] * influence
        
        # Simple correction de distance
        if sensors[sensor_right] < 0.2:  # Trop proche
            left_speed += 0.3
            right_speed -= 0.3
        elif sensors[sensor_right] > 0.4:  # Trop loin
            left_speed -= 0.2
            right_speed += 0.2
        
        left_speed = max(-1.0, min(1.0, left_speed))
        right_speed = max(-1.0, min(1.0, right_speed))
        
        return left_speed, right_speed, False
    
    # ============================================
    # COMPORTEMENT 3: CHERCHEUR DE ZONES (ZONE SEEKER)
    # ============================================
    def zone_seeker_behavior(self, sensors, sensor_team):
        """
        Attiré par les zones ennemies (rouges).
        Poids: attraction vers le rouge.
        """
        if sensor_team is None:
            # Si pas d'info, avance droit
            return 0.7, 0.7, False
        
        base_speed = 0.6
        left_speed = base_speed
        right_speed = base_speed
        
        # Détecter les zones ennemies
        enemy_left = 0
        enemy_right = 0
        
        # Capteurs gauche (0,1,2,7)
        for i in [sensor_back_left, sensor_left, sensor_front_left, sensor_back]:
            if i < len(sensor_team) and sensor_team[i] != "n/a" and sensor_team[i] != self.team:
                enemy_left += 1
        
        # Capteurs droit (4,5,6)
        for i in [sensor_front_right, sensor_right, sensor_back_right]:
            if i < len(sensor_team) and sensor_team[i] != "n/a" and sensor_team[i] != self.team:
                enemy_right += 1
        
        # Poids Braitenberg purs
        # Plus de rouge à gauche: tourne à gauche
        # Plus de rouge à droite: tourne à droite
        left_turn = enemy_right - enemy_left  # Rouge à droite → tourne à gauche
        right_turn = enemy_left - enemy_right # Rouge à gauche → tourne à droite
        
        left_speed += left_turn * 0.2
        right_speed += right_turn * 0.2
        
        # Si aucun ennemi, tourne légèrement pour chercher
        if enemy_left == 0 and enemy_right == 0:
            # Utilise memory pour alterner direction de recherche
            if self.memory % 100 < 50:
                left_speed += 0.1
                right_speed -= 0.1
            else:
                left_speed -= 0.1
                right_speed += 0.1
        
        self.memory += 1
        
        left_speed = max(-1.0, min(1.0, left_speed))
        right_speed = max(-1.0, min(1.0, right_speed))
        
        return left_speed, right_speed, False
    
    # ============================================
    # COMPORTEMENT 4: AGRESSIF (ATTACKER)
    # ============================================
    def aggressive_behavior(self, sensors, sensor_view, sensor_team):
        """
        Combine évitement murs et attraction zones.
        Poids mixtes.
        """
        base_speed = 0.8  # Plus rapide
        left_speed = base_speed
        right_speed = base_speed
        
        sensor_values = [1.0 - d for d in sensors]
        
        # PARTIE 1: Éviter les murs (comme coward)
        if sensor_view:
            for i in range(8):
                if sensor_view[i] == 1:  # Mur
                    influence = sensor_values[i]
                    # Poids simples
                    if i in [sensor_back_left, sensor_left, sensor_front_left]:
                        left_speed -= influence * 0.5  # Mur gauche ralentit gauche
                    elif i in [sensor_front_right, sensor_right, sensor_back_right]:
                        right_speed -= influence * 0.5  # Mur droit ralentit droit
                    elif i == sensor_front:
                        left_speed -= influence * 0.3
                        right_speed -= influence * 0.3
        
        # PARTIE 2: Chercher zones ennemies
        if sensor_team:
            left_red = 0
            right_red = 0
            
            for i in range(8):
                if sensor_team[i] != "n/a" and sensor_team[i] != self.team:
                    if i in [sensor_back_left, sensor_left, sensor_front_left, sensor_back]:
                        left_red += 1
                    elif i in [sensor_front_right, sensor_right, sensor_back_right]:
                        right_red += 1
                    elif i == sensor_front:
                        left_red += 1
                        right_red += 1
            
            # Attraction vers le rouge
            # Rouge à droite: accélère gauche pour tourner vers la droite
            left_speed += right_red * 0.2
            # Rouge à gauche: accélère droite pour tourner vers la gauche
            right_speed += left_red * 0.2
        
        # PARTIE 3: Anti-blocage
        if sensors[sensor_front] < 0.15:
            # Mur très proche devant
            left_speed = 0.3
            right_speed = -0.3
        
        left_speed = max(-1.0, min(1.0, left_speed))
        right_speed = max(-1.0, min(1.0, right_speed))
        
        return left_speed, right_speed, False

# ============================================
# VERSION ULTRA-SIMPLE POUR DÉBUTER
# ============================================
class Robot_braitenberg_basic(Robot):
    """
    Braitenberg le plus simple possible.
    Un seul comportement avec poids -1, 0, 1.
    """
    
    def step(self, sensors, sensor_view=None, sensor_robot=None, sensor_team=None):
        # Configuration de base
        base_speed = 0.5
        
        # Poids BRUT Braitenberg (véhicule 2a de Braitenberg)
        # Capteur gauche → Moteur gauche: -1 (inhibition)
        # Capteur droit → Moteur droit: -1 (inhibition)
        
        left_speed = base_speed
        right_speed = base_speed
        
        # Utilise seulement les 2 capteurs avant
        left_sensor = sensors[sensor_front_left]  # Capteur avant-gauche
        right_sensor = sensors[sensor_front_right] # Capteur avant-droit
        
        # Conversion: 0=proche, 1=loin → on veut l'inverse pour Braitenberg
        left_stimulus = 1.0 - left_sensor  # 1.0 si proche, 0.0 si loin
        right_stimulus = 1.0 - right_sensor
        
        # Application des poids -1
        left_speed += (-1) * left_stimulus  # Obstacle gauche ralentit gauche
        right_speed += (-1) * right_stimulus # Obstacle droit ralentit droit
        
        # Ajout d'un peu de comportement de zone
        if sensor_team:
            # Si rouge devant, accélère
            if (sensor_team[sensor_front] != "n/a" and 
                sensor_team[sensor_front] != self.team):
                left_speed += 0.3
                right_speed += 0.3
        
        # Limites
        left_speed = max(-1.0, min(1.0, left_speed))
        right_speed = max(-1.0, min(1.0, right_speed))
        
        return left_speed, right_speed, False

# ============================================
# VÉHICULES BRAITENBERG CANONIQUES
# ============================================
class Robot_braitenberg_vehicle(Robot):
    """
    Implémentation exacte des véhicules de Braitenberg.
    """
    
    def __init__(self, x_0, y_0, theta_0, name="n/a", team="n/a"):
        super().__init__(x_0, y_0, theta_0, name, team)
        # Type de véhicule Braitenberg
        # 0: Coward (2a), 1: Aggressive (2b), 2: Love (3a), 3: Explorer (3b)
        self.vehicle_type = self.robot_id % 4
    
    def step(self, sensors, sensor_view=None, sensor_robot=None, sensor_team=None):
        
        if self.vehicle_type == 0:
            # VÉHICULE 2a: COWARD (peureux)
            # Capteur → Moteur même côté: connexion inhibitrice (-1)
            return self.vehicle_2a(sensors)
        
        elif self.vehicle_type == 1:
            # VÉHICULE 2b: AGGRESSIVE (agressif)
            # Capteur → Moteur opposé: connexion excitatoire (+1)
            return self.vehicle_2b(sensors)
        
        elif self.vehicle_type == 2:
            # VÉHICULE 3a: LOVE (amoureux)
            # Capteur → Moteur même côté: connexion excitatoire (+1)
            return self.vehicle_3a(sensors, sensor_team)
        
        else:  # vehicle_type == 3
            # VÉHICULE 3b: EXPLORER (explorateur)
            # Capteur → Moteur opposé: connexion inhibitrice (-1)
            return self.vehicle_3b(sensors, sensor_team)
    
    def vehicle_2a(self, sensors):
        """Véhicule 2a: Coward - Fuit la lumière/obstacles"""
        base = 0.6
        # Deux capteurs seulement (gauche/droit)
        left_stim = 1.0 - sensors[sensor_front_left]
        right_stim = 1.0 - sensors[sensor_front_right]
        
        # Connexions: même côté, inhibitrices (-1)
        left_speed = base + (-1) * left_stim
        right_speed = base + (-1) * right_stim
        
        return left_speed, right_speed, False
    
    def vehicle_2b(self, sensors):
        """Véhicule 2b: Aggressive - Va vers la lumière/obstacles"""
        base = 0.4  # Plus lent pour être "agressif" vers les obstacles
        left_stim = 1.0 - sensors[sensor_front_left]
        right_stim = 1.0 - sensors[sensor_front_right]
        
        # Connexions: côté opposé, excitatoires (+1)
        left_speed = base + (+1) * right_stim  # Droit → Gauche
        right_speed = base + (+1) * left_stim  # Gauche → Droit
        
        return left_speed, right_speed, False
    
    def vehicle_3a(self, sensors, sensor_team):
        """Véhicule 3a: Love - Aime la lumière (zones rouges)"""
        base = 0.5
        
        # Stimulus des zones
        left_red = 0
        right_red = 0
        
        if sensor_team:
            # Rouge à gauche?
            if (sensor_team[sensor_front_left] != "n/a" and 
                sensor_team[sensor_front_left] != self.team):
                left_red = 1.0
            # Rouge à droite?
            if (sensor_team[sensor_front_right] != "n/a" and 
                sensor_team[sensor_front_right] != self.team):
                right_red = 1.0
        
        # Connexions: même côté, excitatoires (+1)
        left_speed = base + (+1) * left_red
        right_speed = base + (+1) * right_red
        
        # Si pas de rouge, avance doucement
        if left_red == 0 and right_red == 0:
            left_speed = base
            right_speed = base
        
        return left_speed, right_speed, False
    
    def vehicle_3b(self, sensors, sensor_team):
        """Véhicule 3b: Explorer - Explore la lumière (zones)"""
        base = 0.5
        
        left_red = 0
        right_red = 0
        
        if sensor_team:
            if (sensor_team[sensor_front_left] != "n/a" and 
                sensor_team[sensor_front_left] != self.team):
                left_red = 1.0
            if (sensor_team[sensor_front_right] != "n/a" and 
                sensor_team[sensor_front_right] != self.team):
                right_red = 1.0
        
        # Connexions: côté opposé, inhibitrices (-1)
        left_speed = base + (-1) * right_red  # Rouge droit inhibe gauche
        right_speed = base + (-1) * left_red  # Rouge gauche inhibe droit
        
        # Si pas de rouge, tourne pour chercher
        if left_red == 0 and right_red == 0:
            # Utilise memory pour alterner
            if self.memory % 100 < 50:
                left_speed += 0.2
                right_speed -= 0.2
            else:
                left_speed -= 0.2
                right_speed += 0.2
            
            self.memory += 1
        
        return left_speed, right_speed, False