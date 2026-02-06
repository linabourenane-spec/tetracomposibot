# Projet "robotique" IA&Jeux 2025
#
# Binome:
#  Prénom Nom No_étudiant/e : _________
#  Prénom Nom No_étudiant/e : _________

from robot import *
import math
import random

nb_robots = 0


class Robot_player(Robot):
    team_name = "NeuroBot"  # Nom de votre équipe
    robot_id = -1
    memory = 0
    # Paramètres d'apprentissage
    it_per_evaluation = 400  # Nombre de pas pour tester une stratégie
    evaluations = 500  # Nombre total d'essais (générations)

    def __init__(self, x_0, y_0, theta_0, name="n/a", team="n/a", evaluations=0, it_per_evaluation=0):
        global nb_robots
        self.robot_id = nb_robots
        nb_robots += 1
        super().__init__(x_0, y_0, theta_0, name="Robot " + str(self.robot_id), team=self.team_name)

        # Paramètres pour le calcul de la couverture
        self.occupancy_scale = 4  # Même que dans tetracomposibot.py
        self.arena_size = 100
        self.particle_box = 2

        # --- Initialisation Génétique ---
        # Taille du génome : (25 entrées * 5 cachés) + 5 biais + (5 cachés * 2 sorties) + 2 biais = 142
        self.genome_size = 142
        self.genome = [random.uniform(-1, 1) for _ in range(self.genome_size)]

        # On sauvegarde le meilleur résultat
        self.best_genome = self.genome[:]
        self.best_score = -1000

        # Suivi de la couverture
        self.visited_cells = set()  # Cellules visitées pendant l'évaluation

        # Variables de suivi
        self.trial = 0
        self.iteration = 0
        self.current_score = 0

        # Pour le calcul de la fitness
        self.last_x = x_0
        self.last_y = y_0
        self.last_theta = theta_0

        # Statistiques de l'évaluation
        self.distance_traveled = 0
        self.cells_visited = 0

        # Permet de passer les paramètres depuis config_TP2
        if evaluations > 0:
            self.evaluations = evaluations
        else:
            self.evaluations = 500

        if it_per_evaluation > 0:
            self.it_per_evaluation = it_per_evaluation
        else:
            self.it_per_evaluation = 400

    def reset(self):
        super().reset()
        # On réinitialise la position précédente et les cellules visitées
        self.last_x = self.x
        self.last_y = self.y
        self.last_theta = self.theta
        self.visited_cells.clear()
        self.distance_traveled = 0
        self.cells_visited = 0

    def mutate(self, parent_genome):
        """ Crée un enfant en modifiant légèrement le parent (Mutation) """
        child = parent_genome[:]
        # Taux de mutation : on modifie environ 10% des gènes
        mutation_rate = 0.1
        for i in range(len(child)):
            if random.random() < mutation_rate:
                # Ajout d'un petit bruit ou remplacement
                child[i] += random.gauss(0, 0.5)
                # On clamp pour rester entre -1 et 1 (optionnel mais souvent mieux)
                child[i] = max(-1, min(1, child[i]))
        return child

    def calculate_cell_position(self, x, y):
        """Calcule la position de la cellule dans la grille de couverture"""
        # Centre du robot
        center_y = int(y + self.particle_box / 2.0)
        center_x = int(x + self.particle_box / 2.0)

        # Coordonnées dans la grille réduite (occupancy_small)
        small_y = center_y // self.occupancy_scale
        small_x = center_x // self.occupancy_scale

        # S'assurer que les coordonnées sont dans les limites
        max_cell = (self.arena_size // self.occupancy_scale) - 1
        small_y = max(0, min(small_y, max_cell))
        small_x = max(0, min(small_x, max_cell))

        return (small_y, small_x)

    def step(self, sensors, sensor_view=None, sensor_robot=None, sensor_team=None):
        # ----------------------------------------------------------------
        # 1. CALCUL DE LA FITNESS POUR PAINT WARS
        # ----------------------------------------------------------------
        # La fitness optimise la couverture territoriale et l'exploration

        # a) Calcul du déplacement réel
        dist_reelle = math.sqrt((self.x - self.last_x) ** 2 + (self.y - self.last_y) ** 2)
        rot_reelle = abs(self.theta - self.last_theta)

        # Mise à jour des statistiques de déplacement
        self.distance_traveled += dist_reelle

        # b) Score de couverture - le plus important pour Paint Wars
        cell_pos = self.calculate_cell_position(self.x, self.y)
        if cell_pos not in self.visited_cells:
            self.visited_cells.add(cell_pos)
            self.cells_visited += 1
            # Forte récompense pour chaque nouvelle cellule visitée
            self.current_score += 20.0

        # c) Score d'exploration (déplacement)
        # Récompense le mouvement, surtout s'il est en ligne droite
        if dist_reelle > 0.1:  # Seuil minimum de déplacement
            movement_score = dist_reelle * (1.0 - min(1.0, rot_reelle / 15.0))
            self.current_score += movement_score * 2.0

        # d) Évitement des obstacles (pour éviter de rester bloqué)
        # Détection d'obstacles proches
        front_obstacle = (sensor_view[sensor_front] == 1 or
                          sensor_view[sensor_front_left] == 1 or
                          sensor_view[sensor_front_right] == 1)

        if front_obstacle and sensors[sensor_front] < 0.3:
            # Pénalité si très proche d'un mur
            self.current_score -= 5.0
        elif front_obstacle and sensors[sensor_front] < 0.6:
            # Légère pénalité si obstacle à distance moyenne
            self.current_score -= 1.0

        # e) Récompense pour éviter les collisions avec d'autres robots
        robot_in_front = (sensor_view[sensor_front] == 2 or
                          sensor_view[sensor_front_left] == 2 or
                          sensor_view[sensor_front_right] == 2)

        if robot_in_front and sensors[sensor_front] < 0.4:
            # Pénalité si trop proche d'un autre robot
            self.current_score -= 3.0

        # f) Bonus pour explorer différentes directions
        # Pas de pénalité pour rotation modérée, légère pénalité pour rotation excessive
        if rot_reelle > 30.0:
            self.current_score -= rot_reelle * 0.1

        # Mise à jour positions précédentes
        self.last_x = self.x
        self.last_y = self.y
        self.last_theta = self.theta

        # ----------------------------------------------------------------
        # 2. GESTION DE L'EVOLUTION (RESET & OPTIMISATION)
        # ----------------------------------------------------------------
        if self.iteration >= self.it_per_evaluation:
            # Fin de l'essai courant, on évalue

            # Score final avec bonus pour la diversité des cellules visitées
            coverage_bonus = self.cells_visited * 5.0
            exploration_bonus = min(self.distance_traveled / 10.0, 100.0)

            final_score = self.current_score + coverage_bonus + exploration_bonus
            normalized_score = final_score / self.iteration if self.iteration > 0 else 0

            if normalized_score > self.best_score:
                print(f"--> NEW RECORD (Trial {self.trial})! Score: {normalized_score:.2f}")
                print(f"   Cells: {self.cells_visited}, Distance: {self.distance_traveled:.1f}")
                self.best_genome = self.genome[:]  # Sauvegarde du champion
                self.best_score = normalized_score

            self.trial += 1

            if self.trial < self.evaluations:
                # On tente une mutation du meilleur génome trouvé jusqu'ici
                self.genome = self.mutate(self.best_genome)
            else:
                # Fin de l'entraînement : on joue le champion à l'infini
                self.genome = self.best_genome[:]
                self.it_per_evaluation = 999999  # Ne plus jamais reset
                print("*** TRAINING FINISHED : REPLAYING BEST STRATEGY ***")
                print(f"Best genome score: {self.best_score:.2f}")
                self.save_best_genome()

            # Reset des compteurs pour le prochain essai
            self.current_score = 0
            self.iteration = 0
            self.visited_cells.clear()
            self.distance_traveled = 0
            self.cells_visited = 0

            # Demande de reset au simulateur (replace le robot au départ)
            return 0, 0, True

        # ----------------------------------------------------------------
        # 3. RÉSEAU DE NEURONES (FORWARD PASS)
        # ----------------------------------------------------------------

        # --- A. Préparation des Entrées (25 inputs) ---
        inputs = []
        # 8 distances
        inputs.extend(sensors)
        # 8 murs (1.0 si mur, 0.0 sinon)
        inputs.extend([1.0 if v == 1 else 0.0 for v in sensor_view])
        # 8 ennemis (1.0 si ennemi, 0.0 sinon)
        inputs.extend([1.0 if (t != "n/a" and t != self.team) else 0.0 for t in sensor_team])
        # 1 mémoire
        inputs.append(float(self.memory))

        # --- B. Couche Cachée (Hidden Layer) ---
        # Structure: 25 entrées -> 5 neurones
        hidden_outputs = []
        nb_hidden = 5
        idx = 0  # Pointeur de lecture dans le génome

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
        # Structure: 5 cachés -> 2 sorties (Translation, Rotation)
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
            # Fonction d'activation (-1 à 1)
            outputs.append(math.tanh(activation))

        # Récupération des commandes
        translation = outputs[0]
        rotation = outputs[1]

        # Ajouter un peu de bruit pour l'exploration pendant l'entraînement
        if self.trial < self.evaluations:
            translation += random.uniform(-0.1, 0.1)
            rotation += random.uniform(-0.1, 0.1)

        # Limiter les valeurs
        translation = max(-1.0, min(1.0, translation))
        rotation = max(-1.0, min(1.0, rotation))

        # Incrément du compteur de temps
        self.iteration += 1

        return translation, rotation, False

    # Dans robot_challenger_training.py, ajouter à la fin de step() ou dans __init__()

    def save_best_genome(self, filename="my_best_genome.txt"):
        """Sauvegarde le meilleur génome dans un fichier"""
        with open(filename, 'w') as f:
            for gene in self.best_genome:
                f.write(f"{gene:.6f}\n")
        print(f"Best genome saved to {filename}")