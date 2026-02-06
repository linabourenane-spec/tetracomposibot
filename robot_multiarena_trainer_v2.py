# Projet "robotique" IA&Jeux 2025
# Entraînement multi-arènes avec changements dynamiques
#
# Binome:
#  Prénom Nom No_étudiant/e : _________
#  Prénom Nom No_étudiant/e : _________

from robot import *
import math
import random
import json
import os
from datetime import datetime

nb_robots = 0


class Robot_player(Robot):
    team_name = "MultiArenaMaster"
    robot_id = -1
    memory = 0

    # Configuration des arènes d'entraînement
    TRAINING_ARENAS = [0, 1, 2, 3, 4]  # Arènes de base
    current_arena_index = 0

    # Compteurs
    evaluations = 1000  # Total
    evaluations_per_arena = 200  # Évaluations par arène avant changement
    it_per_evaluation = 400  # Pas par évaluation

    def __init__(self, x_0, y_0, theta_0, name="n/a", team="n/a", evaluations=0, it_per_evaluation=0):
        global nb_robots
        self.robot_id = nb_robots
        nb_robots += 1
        super().__init__(x_0, y_0, theta_0, name="Robot " + str(self.robot_id), team=self.team_name)

        # Paramètres
        self.occupancy_scale = 4
        self.arena_size = 100
        self.particle_box = 2

        # --- Génétique ---
        self.genome_size = 142
        self.genome = [random.uniform(-1, 1) for _ in range(self.genome_size)]

        # Meilleurs scores
        self.best_genome = self.genome[:]
        self.best_score = -1000

        # Scores par arène
        self.arena_scores = {arena: [] for arena in self.TRAINING_ARENAS}
        self.arena_best_scores = {arena: -1000 for arena in self.TRAINING_ARENAS}
        self.arena_best_genomes = {arena: self.genome[:] for arena in self.TRAINING_ARENAS}

        # Variables d'état
        self.trial = 0
        self.iteration = 0
        self.current_score = 0
        self.evaluations_in_current_arena = 0

        # Tracking
        self.visited_cells = set()
        self.distance_traveled = 0
        self.cells_visited = 0
        self.last_x = x_0
        self.last_y = y_0
        self.last_theta = theta_0

        # Historique
        self.training_history = []

        # Override depuis config
        if evaluations > 0:
            self.evaluations = evaluations
        if it_per_evaluation > 0:
            self.it_per_evaluation = it_per_evaluation

        print(f"Multi-arena training initialized. Arenas: {self.TRAINING_ARENAS}")
        print(f"Will train for {self.evaluations} evaluations total")
        print(f"Changing arena every {self.evaluations_per_arena} evaluations")

    def reset(self):
        super().reset()
        self.last_x = self.x
        self.last_y = self.y
        self.last_theta = self.theta
        self.visited_cells.clear()
        self.distance_traveled = 0
        self.cells_visited = 0
        self.current_score = 0

    def mutate(self, parent_genome):
        """Mutation adaptative"""
        child = parent_genome[:]
        mutation_rate = 0.1

        # Augmenter mutation si performance faible
        if self.best_score < 50:
            mutation_rate = 0.2

        for i in range(len(child)):
            if random.random() < mutation_rate:
                child[i] += random.gauss(0, 0.3)
                child[i] = max(-1, min(1, child[i]))

        return child

    def calculate_cell_position(self, x, y):
        """Calcule position dans la grille de couverture"""
        center_y = int(y + self.particle_box / 2.0)
        center_x = int(x + self.particle_box / 2.0)

        small_y = center_y // self.occupancy_scale
        small_x = center_x // self.occupancy_scale

        max_cell = (self.arena_size // self.occupancy_scale) - 1
        small_y = max(0, min(small_y, max_cell))
        small_x = max(0, min(small_x, max_cell))

        return (small_y, small_x)

    def should_change_arena(self):
        """Détermine si on doit changer d'arène"""
        return self.evaluations_in_current_arena >= self.evaluations_per_arena

    def get_next_arena(self):
        """Passe à l'arène suivante"""
        self.current_arena_index = (self.current_arena_index + 1) % len(self.TRAINING_ARENAS)
        self.evaluations_in_current_arena = 0

        arena = self.TRAINING_ARENAS[self.current_arena_index]
        print(f"\n{'=' * 60}")
        print(f"SWITCHING TO ARENA {arena}")
        print(f"{'=' * 60}\n")

        return arena

    def compute_fitness(self, sensors, sensor_view):
        """Calcule le score de fitness"""
        # 1. Couverture territoriale
        cell_pos = self.calculate_cell_position(self.x, self.y)
        if cell_pos not in self.visited_cells:
            self.visited_cells.add(cell_pos)
            self.cells_visited += 1
            self.current_score += 20.0  # Forte récompense

        # 2. Déplacement
        dist_reelle = math.sqrt((self.x - self.last_x) ** 2 + (self.y - self.last_y) ** 2)
        rot_reelle = abs(self.theta - self.last_theta)

        self.distance_traveled += dist_reelle

        if dist_reelle > 0.05:
            efficiency = 1.0 - min(1.0, rot_reelle / 15.0)
            self.current_score += dist_reelle * efficiency * 2.0

        # 3. Évitement d'obstacles
        front_clear = True
        for i in [sensor_front, sensor_front_left, sensor_front_right]:
            if sensor_view[i] == 1 and sensors[i] < 0.3:
                self.current_score -= 5.0
                front_clear = False

        # 4. Bonus pour exploration
        if front_clear and dist_reelle > 0.2:
            self.current_score += 1.0

        # 5. Pénalité pour être coincé
        if dist_reelle < 0.01 and rot_reelle < 1.0:
            self.current_score -= 0.5

        # Mise à jour positions
        self.last_x = self.x
        self.last_y = self.y
        self.last_theta = self.theta

    def step(self, sensors, sensor_view=None, sensor_robot=None, sensor_team=None):
        # ----------------------------------------------------------------
        # 1. CALCUL DE FITNESS
        # ----------------------------------------------------------------
        self.compute_fitness(sensors, sensor_view)

        # ----------------------------------------------------------------
        # 2. GESTION DE L'ÉVOLUTION ET CHANGEMENT D'ARÈNE
        # ----------------------------------------------------------------
        if self.iteration >= self.it_per_evaluation:
            # Fin de l'évaluation

            # Score final avec bonus
            coverage_bonus = self.cells_visited * 5.0
            exploration_bonus = min(self.distance_traveled / 10.0, 50.0)
            final_score = self.current_score + coverage_bonus + exploration_bonus
            normalized_score = final_score / self.iteration if self.iteration > 0 else 0

            # Enregistrer le score pour l'arène courante
            current_arena = self.TRAINING_ARENAS[self.current_arena_index]
            self.arena_scores[current_arena].append(normalized_score)

            # Mettre à jour meilleur score pour cette arène
            if normalized_score > self.arena_best_scores[current_arena]:
                self.arena_best_scores[current_arena] = normalized_score
                self.arena_best_genomes[current_arena] = self.genome[:]

            # Mettre à jour meilleur global
            if normalized_score > self.best_score:
                self.best_score = normalized_score
                self.best_genome = self.genome[:]
                print(f"Trial {self.trial}: NEW GLOBAL BEST! {normalized_score:.2f} (Arena {current_arena})")

            # Historique
            self.training_history.append({
                'trial': self.trial,
                'arena': current_arena,
                'score': normalized_score,
                'best_score': self.best_score,
                'cells': self.cells_visited,
                'distance': self.distance_traveled
            })

            self.trial += 1
            self.evaluations_in_current_arena += 1

            # Vérifier si on doit changer d'arène
            if self.should_change_arena():
                # Créer un génome hybride pour la nouvelle arène
                old_arena = current_arena
                new_arena = self.get_next_arena()

                # 70% du meilleur global + 30% du meilleur de la nouvelle arène
                hybrid = []
                for i in range(len(self.best_genome)):
                    if random.random() < 0.7:
                        hybrid.append(self.best_genome[i])
                    else:
                        hybrid.append(self.arena_best_genomes[new_arena][i])

                self.genome = self.mutate(hybrid)

                print(f"Hybrid genome created for Arena {new_arena}")
                print(f"Previous best on Arena {old_arena}: {self.arena_best_scores[old_arena]:.2f}")
            else:
                # Mutation normale
                self.genome = self.mutate(self.best_genome)

            # Fin de l'entraînement
            if self.trial >= self.evaluations:
                self.finish_training()
                return 0, 0, True

            # Reset pour prochaine évaluation
            self.reset()
            self.iteration = 0

            return 0, 0, True

        # ----------------------------------------------------------------
        # 3. RÉSEAU DE NEURONES
        # ----------------------------------------------------------------
        # Préparation des entrées
        inputs = []
        inputs.extend(sensors)  # 8 distances
        inputs.extend([1.0 if v == 1 else 0.0 for v in sensor_view])  # 8 murs
        inputs.extend([1.0 if (t != "n/a" and t != self.team) else 0.0 for t in sensor_team])  # 8 ennemis
        inputs.append(float(self.memory) / 100.0)  # 1 mémoire

        # Forward pass
        hidden_outputs = []
        nb_hidden = 5
        idx = 0

        for h in range(nb_hidden):
            activation = 0
            for inp in inputs:
                activation += inp * self.genome[idx]
                idx += 1
            activation += self.genome[idx]
            idx += 1
            hidden_outputs.append(math.tanh(activation))

        outputs = []
        nb_outputs = 2

        for o in range(nb_outputs):
            activation = 0
            for h_out in hidden_outputs:
                activation += h_out * self.genome[idx]
                idx += 1
            activation += self.genome[idx]
            idx += 1
            outputs.append(math.tanh(activation))

        # Commandes avec bruit d'exploration
        translation = outputs[0]
        rotation = outputs[1]

        if self.trial < self.evaluations:
            noise_level = max(0.05, 0.2 * (1.0 - self.trial / self.evaluations))
            translation += random.uniform(-noise_level, noise_level)
            rotation += random.uniform(-noise_level, noise_level)

        # Limites
        translation = max(-1.0, min(1.0, translation))
        rotation = max(-1.0, min(1.0, rotation))

        self.iteration += 1
        return translation, rotation, False

    def finish_training(self):
        """Termine l'entraînement et sauvegarde les résultats"""
        print("\n" + "=" * 70)
        print("MULTI-ARENA TRAINING COMPLETE!")
        print("=" * 70)

        print(f"\nTotal evaluations: {self.trial}")
        print(f"Best global score: {self.best_score:.2f}")

        print("\nBest scores per arena:")
        for arena in sorted(self.TRAINING_ARENAS):
            best = self.arena_best_scores[arena]
            avg = sum(self.arena_scores[arena]) / len(self.arena_scores[arena]) if self.arena_scores[arena] else 0
            print(f"  Arena {arena}: Best={best:.2f}, Avg={avg:.2f}")

        # Sauvegarde
        self.save_results()

        print("\nResults saved to 'multiarena_training_results.json'")
        print("Best genome saved to 'multiarena_best_genome.txt'")
        print("=" * 70 + "\n")

        # Passer en mode replay avec le meilleur génome
        self.genome = self.best_genome[:]
        self.it_per_evaluation = 999999

    def save_results(self):
        """Sauvegarde tous les résultats d'entraînement"""
        # Fichier JSON complet
        results = {
            'timestamp': datetime.now().isoformat(),
            'best_genome': self.best_genome,
            'best_score': self.best_score,
            'arena_best_scores': self.arena_best_scores,
            'arena_best_genomes': {str(k): v for k, v in self.arena_best_genomes.items()},
            'training_params': {
                'evaluations': self.evaluations,
                'evaluations_per_arena': self.evaluations_per_arena,
                'it_per_evaluation': self.it_per_evaluation,
                'training_arenas': self.TRAINING_ARENAS
            },
            'training_history': self.training_history,
            'arena_scores': {str(k): v for k, v in self.arena_scores.items()}
        }

        with open('multiarena_training_results.json', 'w') as f:
            json.dump(results, f, indent=2)

        # Fichier texte simple pour le génome
        with open('multiarena_best_genome.txt', 'w') as f:
            for gene in self.best_genome:
                f.write(f"{gene:.6f}\n")

        # Fichier CSV pour analyse
        with open('multiarena_training_stats.csv', 'w') as f:
            f.write("trial,arena,score,best_score,cells,distance\n")
            for entry in self.training_history:
                f.write(f"{entry['trial']},{entry['arena']},{entry['score']:.2f},"
                        f"{entry['best_score']:.2f},{entry['cells']},{entry['distance']:.2f}\n")

    def load_trained_genome(self, filename="multiarena_best_genome.txt"):
        """Charge un génome entraîné"""
        try:
            with open(filename, 'r') as f:
                genome = [float(line.strip()) for line in f.readlines()]

            if len(genome) == self.genome_size:
                self.genome = genome
                self.best_genome = genome[:]
                print(f"Loaded trained genome from {filename}")
                return True
        except FileNotFoundError:
            print(f"File {filename} not found")

        return False


# Version pour Paint Wars avec le génome entraîné
class MultiArenaChampion(Robot_player):
    """Robot qui utilise le génome multi-arènes entraîné"""

    def __init__(self, x_0, y_0, theta_0, name="n/a", team="n/a"):
        super().__init__(x_0, y_0, theta_0, name, team)

        # Charger le génome entraîné
        if not self.load_trained_genome("multiarena_best_genome.txt"):
            print("Using default genome")

        # Mode jeu (pas d'entraînement)
        self.training_complete = True

        # Stratégie Paint Wars
        self.enemy_memory = {}
        self.territory_memory = set()
        self.mode = "explore"  # explore, chase, avoid

    def step(self, sensors, sensor_view=None, sensor_robot=None, sensor_team=None):
        # Détection d'ennemis
        enemy_detected = False
        enemy_direction = 0

        for i in range(len(sensor_team)):
            if sensor_team[i] != "n/a" and sensor_team[i] != self.team:
                enemy_detected = True
                enemy_direction = i
                break

        # Stratégie adaptative
        if enemy_detected and sensors[enemy_direction] < 0.5:
            self.mode = "chase"
        elif sensors[sensor_front] < 0.2:
            self.mode = "avoid"
        else:
            self.mode = "explore"

        # Réseau neuronal de base
        inputs = []
        inputs.extend(sensors)
        inputs.extend([1.0 if v == 1 else 0.0 for v in sensor_view])
        inputs.extend([1.0 if (t != "n/a" and t != self.team) else 0.0 for t in sensor_team])
        inputs.append(1.0 if self.mode == "chase" else -1.0 if self.mode == "avoid" else 0.0)

        # Forward pass
        hidden_outputs = []
        nb_hidden = 5
        idx = 0

        for h in range(nb_hidden):
            activation = 0
            for inp in inputs:
                activation += inp * self.genome[idx]
                idx += 1
            activation += self.genome[idx]
            idx += 1
            hidden_outputs.append(math.tanh(activation))

        outputs = []
        nb_outputs = 2

        for o in range(nb_outputs):
            activation = 0
            for h_out in hidden_outputs:
                activation += h_out * self.genome[idx]
                idx += 1
            activation += self.genome[idx]
            idx += 1
            outputs.append(math.tanh(activation))

        translation, rotation = outputs[0], outputs[1]

        # Ajustements tactiques
        if self.mode == "chase" and enemy_detected:
            # Suivre l'ennemi
            if enemy_direction == sensor_front_left:
                rotation -= 0.3
            elif enemy_direction == sensor_front_right:
                rotation += 0.3
            translation = min(1.0, translation * 1.2)

        elif self.mode == "avoid":
            # Éviter l'obstacle
            if sensors[sensor_front_left] < sensors[sensor_front_right]:
                rotation += 0.5
            else:
                rotation -= 0.5
            translation *= 0.7

        # Limites
        translation = max(-1.0, min(1.0, translation))
        rotation = max(-1.0, min(1.0, rotation))

        return translation, rotation, False