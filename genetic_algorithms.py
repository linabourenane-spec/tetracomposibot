from robot import *
import math
import random
import copy

nb_robots = 0

class Robot_player(Robot):
    
    team_name = "Optimizer"
    

    it_per_round = 400    
    rounds_per_gene = 3    
    max_generations = 500   
    
    def __init__(self, x_0, y_0, theta_0, name="n/a", team="n/a", evaluations=0, it_per_evaluation=0):
        global nb_robots
        self.robot_id = nb_robots
        nb_robots += 1
        
        super().__init__(x_0, y_0, theta_0, name=name, team=team)
        
        self.x_0, self.y_0, self.theta_0 = x_0, y_0, theta_0
        

        

        self.parent_param = [random.randint(-1, 1) for i in range(8)]
        self.parent_score = -float('inf')
        

        self.current_param = self.parent_param[:]
        self.is_evaluating_parent = True 
        
    
        self.generation = 0        
        self.run_count = 0        
        
        
        self.current_round_score = 0
        self.gene_total_score = 0   
        
  
        self.iteration = 0
        self.last_x, self.last_y, self.last_theta = x_0, y_0, theta_0

    def get_mutation(self, params):
        """
        Opérateur de mutation : Modifie un seul gène, valeur forcément différente.
        """
        child = params[:] 
        
       
        idx = random.randint(0, 7)
        old_val = child[idx]
        
 
        options = [-1, 0, 1]
        options.remove(old_val) 
        child[idx] = random.choice(options) 
        
        return child

    def reset(self):
        super().reset()
       
        self.theta = random.uniform(0, 360)
        
        self.iteration = 0
        self.current_round_score = 0
        self.last_x, self.last_y, self.last_theta = self.x, self.y, self.theta

    def step(self, sensors, sensor_view=None, sensor_robot=None, sensor_team=None):
        

        dist_reelle = math.sqrt((self.x - self.last_x)**2 + (self.y - self.last_y)**2)
        rot_reelle = abs(self.theta - self.last_theta)
        
        self.last_x, self.last_y, self.last_theta = self.x, self.y, self.theta
        self.current_round_score += dist_reelle * (1 - rot_reelle)

        

        time_limit = 1000 if self.generation >= self.max_generations else self.it_per_round

        if self.iteration >= time_limit:
            
   
            self.gene_total_score += self.current_round_score
            self.run_count += 1
            

            if self.generation < self.max_generations and self.run_count < self.rounds_per_gene:
                return 0, 0, True


            else:
                score_final = self.gene_total_score
                
 
                if self.generation < self.max_generations:
                    

                    if self.is_evaluating_parent:
                        print(f"Gen 0 (Parent Init) | Score : {score_final:.2f}")
                        self.parent_score = score_final
                        self.is_evaluating_parent = False
    
                        self.current_param = self.get_mutation(self.parent_param)
                        
 
                    else:
                        print(f"Gen {self.generation} | Parent: {self.parent_score:.2f} vs Enfant: {score_final:.2f}", end="")

                        if score_final >= self.parent_score:
                            print(" -> ENFANT GARDE (Mutation acceptée)")
                            self.parent_score = score_final
                            self.parent_param = self.current_param[:] # L'enfant devient parent
                        else:
                            print(" -> REJET (Retour au parent)")

                        
                        self.generation += 1
                        
                        # --- MUTATION ---
                        if self.generation < self.max_generations:
                            # On crée un nouvel enfant à partir du parent (qui est soit l'ancien, soit le nouveau)
                            self.current_param = self.get_mutation(self.parent_param)


                else:
                    print("*** MODE REPLAY (Meilleur Parent) ***")
                    self.current_param = self.parent_param[:] # On s'assure d'utiliser le champion
                
                # Reset des compteurs pour le prochain individu
                self.run_count = 0
                self.gene_total_score = 0
                return 0, 0, True

 
        
        translation = math.tanh(self.current_param[0] + 
                                self.current_param[1] * sensors[sensor_front_left] + 
                                self.current_param[2] * sensors[sensor_front] + 
                                self.current_param[3] * sensors[sensor_front_right])
        
        rotation = math.tanh(self.current_param[4] + 
                             self.current_param[5] * sensors[sensor_front_left] + 
                             self.current_param[6] * sensors[sensor_front] + 
                             self.current_param[7] * sensors[sensor_front_right])

        self.iteration += 1        

        return translation, rotation, False