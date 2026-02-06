# Projet "robotique" IA&Jeux 2025
#
# Binome:
#  Prénom Nom No_étudiant/e : _________
#  Prénom Nom No_étudiant/e : _________
#
# check robot.py for sensor naming convention
# all sensor and motor value are normalized (from 0.0 to 1.0 for sensors, -1.0 to +1.0 for motors)

from robot import *
import math

nb_robots = 0


class Robot_player(Robot):
    team_name = "Challenger"  # vous pouvez modifier le nom de votre équipe
    robot_id = -1  # ne pas modifier. Permet de connaitre le numéro de votre robot.
    memory = 0  # vous n'avez le droit qu'a une case mémoire qui doit être obligatoirement un entier

    def __init__(self, x_0, y_0, theta_0, name="n/a", team="n/a"):
        global nb_robots
        self.robot_id = nb_robots
        nb_robots += 1
        super().__init__(x_0, y_0, theta_0, name="Robot " + str(self.robot_id), team=self.team_name)
        # Un génome aléatoire de 142 gènes
        self.genome = [random.uniform(-1, 1) for _ in range(142)]

    def step(self, sensors, sensor_view=None, sensor_robot=None, sensor_team=None):
        # 1. PRÉPARATION DES ENTRÉES (INPUTS)
        inputs = []

        # Ajout des distances (8)
        inputs.extend(sensors)

        # Ajout "Est-ce un mur ?" (8)
        inputs.extend([1.0 if v == 1 else 0.0 for v in sensor_view])

        # Ajout "Est-ce un ennemi ?" (8)
        # Note: self.team est accessible dans votre robot
        inputs.extend([1.0 if (t != "n/a" and t != self.team) else 0.0 for t in sensor_team])

        # Ajout Mémoire (1)
        inputs.append(float(self.memory))

        # Total inputs = 25

        # 2. COUCHE CACHÉE (HIDDEN LAYER)
        # Supposons que self.weights_hidden contient les poids optimisés par votre algo génétique
        # Structure de self.weights_hidden : liste de 5 listes de 25 poids (+ biais éventuellement)
        hidden_outputs = []
        nb_hidden = 5

        # Exemple simplifié sans gestion matricielle complexe
        # index_weight est un pointeur pour parcourir votre liste linéaire de gènes (paramètres)
        idx = 0

        for h in range(nb_hidden):
            activation = 0
            for inp in inputs:
                activation += inp * self.genome[idx]  # self.genome est votre liste de paramètres
                idx += 1
            # Ajout d'un biais (optionnel mais recommandé)
            activation += self.genome[idx]
            idx += 1

            # Fonction d'activation (Tanh est souvent utilisée ici)
            hidden_outputs.append(math.tanh(activation))

        # 3. COUCHE DE SORTIE (OUTPUT LAYER)
        outputs = []
        nb_outputs = 2  # Translation, Rotation

        for o in range(nb_outputs):
            activation = 0
            for h_out in hidden_outputs:
                activation += h_out * self.genome[idx]
                idx += 1
            activation += self.genome[idx]  # Biais sortie
            idx += 1
            outputs.append(math.tanh(activation))

        translation = outputs[0]
        rotation = outputs[1]

        return translation, rotation, False
