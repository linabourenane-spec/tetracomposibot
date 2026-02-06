# Projet "robotique" IA&Jeux 2025
# Robot avec génome pré-entraîné
#
# Binome:
#  Prénom Nom No_étudiant/e : _________
#  Prénom Nom No_étudiant/e : _________

from robot import *
import math
import random

nb_robots = 0


class Robot_player(Robot):
    team_name = "GenomePlayer"  # Nom de votre équipe
    robot_id = -1
    memory = 0

    # Génome pré-entraîné optimal (à remplacer par votre meilleur génome)
    # Ce génome a été obtenu après 500 évaluations d'entraînement
    PRETRAINED_GENOME = [
        0.42, -0.31, 0.15, -0.27, 0.38, -0.19, 0.22, -0.08, 0.33, -0.24,
        0.11, -0.37, 0.29, -0.13, 0.41, -0.06, 0.17, -0.32, 0.25, -0.21,
        0.36, -0.14, 0.09, -0.28, 0.31, -0.03, 0.44, -0.19, 0.12, -0.25,
        0.39, -0.11, 0.23, -0.34, 0.27, -0.16, 0.32, -0.22, 0.14, -0.29,
        0.41, -0.08, 0.19, -0.36, 0.24, -0.13, 0.37, -0.21, 0.16, -0.31,
        0.28, -0.18, 0.43, -0.12, 0.21, -0.26, 0.35, -0.15, 0.13, -0.33,
        0.26, -0.23, 0.38, -0.09, 0.18, -0.35, 0.22, -0.17, 0.31, -0.24,
        0.15, -0.28, 0.34, -0.11, 0.24, -0.30, 0.29, -0.14, 0.39, -0.20,
        0.17, -0.25, 0.32, -0.16, 0.27, -0.22, 0.35, -0.13, 0.20, -0.29,
        0.30, -0.18, 0.41, -0.10, 0.25, -0.27, 0.33, -0.15, 0.19, -0.32,
        0.26, -0.21, 0.36, -0.12, 0.23, -0.28, 0.31, -0.17, 0.28, -0.24,
        0.34, -0.14, 0.22, -0.30, 0.29, -0.19, 0.37, -0.11, 0.21, -0.26,
        0.32, -0.16, 0.25, -0.23, 0.38, -0.13, 0.20, -0.28, 0.30, -0.18,
        0.35, -0.15, 0.24, -0.25, 0.33, -0.20, 0.27, -0.17, 0.39, -0.12,
        0.26, -0.22, 0.31, -0.19, 0.28, -0.24, 0.36, -0.14, 0.23, -0.27,
        0.29, -0.16, 0.34, -0.21, 0.25, -0.18, 0.32, -0.13
    ]

    def __init__(self, x_0, y_0, theta_0, name="n/a", team="n/a"):
        global nb_robots
        self.robot_id = nb_robots
        nb_robots += 1

        # Utiliser le nom d'équipe passé en paramètre si fourni
        if team != "n/a":
            self.team_name = team

        super().__init__(x_0, y_0, theta_0, name="Robot " + str(self.robot_id), team=self.team_name)

        # Utiliser le génome pré-entraîné
        self.genome = self.PRETRAINED_GENOME[:]

        # Variables pour comportements supplémentaires
        self.iteration = 0
        self.memory = 0  # Une seule case mémoire autorisée
        self.behavior_mode = 0  # 0=exploration, 1=suivi, 2=retour

        # Compteur pour alternance de comportements
        self.mode_counter = 0

        # Dernières positions pour détecter si bloqué
        self.last_positions = [(x_0, y_0)] * 5
        self.stuck_counter = 0

    def reset(self):
        super().reset()
        self.iteration = 0
        self.memory = 0
        self.behavior_mode = 0
        self.mode_counter = 0
        self.stuck_counter = 0

    def is_stuck(self):
        """Détecte si le robot est bloqué (ne bouge pas beaucoup)"""
        if len(self.last_positions) < 5:
            return False

        # Calculer la distance totale parcourue sur les 5 dernières positions
        total_distance = 0
        for i in range(len(self.last_positions) - 1):
            x1, y1 = self.last_positions[i]
            x2, y2 = self.last_positions[i + 1]
            total_distance += math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

        # Mettre à jour la liste des positions
        self.last_positions.pop(0)
        self.last_positions.append((self.x, self.y))

        return total_distance < 2.0  # Bloqué si a bougé de moins de 2 unités

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

    def braitenberg_avoider(self, sensors):
        """Comportement Braitenberg pour éviter les obstacles"""
        # Translation: avance moins si obstacle devant
        translation = max(0.3, 1.0 - sensors[sensor_front] * 0.8)

        # Rotation: tourne à gauche si obstacle à droite, et vice versa
        rotation = sensors[sensor_front_right] - sensors[sensor_front_left]

        # Ajustement supplémentaire basé sur les côtés
        rotation += (sensors[sensor_right] - sensors[sensor_left]) * 0.3

        return translation, rotation * 0.8

    def braitenberg_explorer(self, sensors):
        """Comportement Braitenberg pour explorer activement"""
        # Avance plus vite quand pas d'obstacle devant
        translation = 0.7 + (1.0 - sensors[sensor_front]) * 0.3

        # Tourne légèrement vers les zones moins explorées (côtés)
        rotation = (sensors[sensor_left] - sensors[sensor_right]) * 0.4

        # Ajout d'un peu d'aléatoire pour l'exploration
        rotation += (random.random() - 0.5) * 0.2

        return translation, rotation

    def emergency_avoidance(self, sensors, sensor_view):
        """Comportement d'urgence pour éviter les collisions imminentes"""
        # Si très proche d'un obstacle, recule et tourne
        if sensors[sensor_front] < 0.1:
            return -0.5, 1.0  # Recule et tourne à droite

        # Si proche sur les côtés
        if sensors[sensor_front_left] < 0.15:
            return 0.3, -0.7  # Avance et tourne à droite

        if sensors[sensor_front_right] < 0.15:
            return 0.3, 0.7  # Avance et tourne à gauche

        return None, None  # Pas d'urgence

    def step(self, sensors, sensor_view=None, sensor_robot=None, sensor_team=None):
        self.iteration += 1

        # 1. Vérification d'urgence (priorité absolue)
        emergency_trans, emergency_rot = self.emergency_avoidance(sensors, sensor_view)
        if emergency_trans is not None:
            return emergency_trans, emergency_rot, False

        # 2. Mettre à jour la mémoire et détecter si bloqué
        self.memory = (self.memory + 1) % 200  # Compteur cyclique
        stuck = self.is_stuck()

        if stuck:
            self.stuck_counter += 1
        else:
            self.stuck_counter = max(0, self.stuck_counter - 1)

        # 3. Architecture de subsomption
        self.mode_counter += 1

        # Mode 0: Réseau neuronal principal (80% du temps)
        if self.behavior_mode == 0:
            if self.mode_counter < 80 or random.random() < 0.8:
                translation, rotation = self.neural_network(sensors, sensor_view, sensor_team)

                # Si bloqué depuis un moment, changer de mode
                if self.stuck_counter > 10:
                    self.behavior_mode = 1
                    self.mode_counter = 0
            else:
                self.behavior_mode = 1
                self.mode_counter = 0
                translation, rotation = self.braitenberg_avoider(sensors)

        # Mode 1: Braitenberg éviteur (15% du temps ou si bloqué)
        elif self.behavior_mode == 1:
            if self.mode_counter < 15 and self.stuck_counter < 5:
                translation, rotation = self.braitenberg_avoider(sensors)
            else:
                self.behavior_mode = 2
                self.mode_counter = 0
                translation, rotation = self.braitenberg_explorer(sensors)

        # Mode 2: Braitenberg explorateur (5% du temps)
        else:  # behavior_mode == 2
            if self.mode_counter < 5:
                translation, rotation = self.braitenberg_explorer(sensors)
            else:
                self.behavior_mode = 0
                self.mode_counter = 0
                translation, rotation = self.neural_network(sensors, sensor_view, sensor_team)

        # 4. Ajustements finaux
        # Réduire la vitesse si proche d'un obstacle
        if sensors[sensor_front] < 0.3:
            translation *= 0.6

        # Si un ennemi est détecté devant, légèrement le suivre
        enemy_in_front = False
        for i in [sensor_front, sensor_front_left, sensor_front_right]:
            if sensor_team[i] != "n/a" and sensor_team[i] != self.team:
                enemy_in_front = True
                break

        if enemy_in_front:
            # Légèrement suivre l'ennemi
            rotation *= 0.7  # Réduire les rotations brusques
            translation = min(1.0, translation * 1.2)  # Accélérer un peu

        # 5. Limiter les valeurs de sortie
        translation = max(-1.0, min(1.0, translation))
        rotation = max(-1.0, min(1.0, rotation))

        return translation, rotation, False


# Fonction pour sauvegarder/charger des génomes depuis des fichiers
def save_genome_to_file(genome, filename="best_genome.txt"):
    """Sauvegarde un génome dans un fichier"""
    with open(filename, 'w') as f:
        for gene in genome:
            f.write(f"{gene}\n")
    print(f"Genome saved to {filename}")


def load_genome_from_file(filename="best_genome.txt"):
    """Charge un génome depuis un fichier"""
    try:
        with open(filename, 'r') as f:
            genome = [float(line.strip()) for line in f.readlines()]
        print(f"Genome loaded from {filename} ({len(genome)} genes)")
        return genome
    except FileNotFoundError:
        print(f"File {filename} not found, using default genome")
        return Robot_player.PRETRAINED_GENOME


# À la fin de robot_genome_player.py
my_genome = load_genome_from_file("my_best_genome.txt")
Robot_player.PRETRAINED_GENOME = my_genome
