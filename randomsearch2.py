from robot import *
import math
import random
import copy

nb_robots = 0

class Robot_player(Robot):
    
    team_name = "Optimizer"
    

    it_per_round = 400      
    rounds_per_strategy = 3 
    max_strategies = 500   
    
    def __init__(self, x_0, y_0, theta_0, name="n/a", team="n/a", evaluations=0, it_per_evaluation=0):
        global nb_robots
        self.robot_id = nb_robots
        nb_robots += 1
        
        super().__init__(x_0, y_0, theta_0, name=name, team=team)
        
        self.x_0, self.y_0, self.theta_0 = x_0, y_0, theta_0
        

        self.param = [random.randint(-1, 1) for i in range(8)]
        
   
        self.bestVec = self.param[:]
        self.bestScore = -10000 
        
     
        self.strategy_count = 0     
        self.run_count = 0          
        
        # Scores
        self.current_round_score = 0 # Score du round actuel
        self.strategy_total_score = 0 # Somme des scores des 3 rounds
        
      
        self.iteration = 0
        self.last_x, self.last_y, self.last_theta = x_0, y_0, theta_0

    def reset(self):

        super().reset()
        
      
        self.theta = random.uniform(0, 360)
    
        self.iteration = 0
        self.current_round_score = 0
        self.last_x = self.x
        self.last_y = self.y
        self.last_theta = self.theta

    def step(self, sensors, sensor_view=None, sensor_robot=None, sensor_team=None):
        
    
        dist_reelle = math.sqrt((self.x - self.last_x)**2 + (self.y - self.last_y)**2)
        rot_reelle = abs(self.theta - self.last_theta)
        
        self.last_x, self.last_y, self.last_theta = self.x, self.y, self.theta
        

        self.current_round_score += dist_reelle * abs(1 - rot_reelle)


        time_limit = 1000 if self.strategy_count >= self.max_strategies else self.it_per_round

        if self.iteration >= time_limit:
            

            self.strategy_total_score += self.current_round_score
            self.run_count += 1
            

            if self.strategy_count < self.max_strategies and self.run_count < self.rounds_per_strategy:

                return 0, 0, True 

  
            else:
            
                if self.strategy_count < self.max_strategies:
                    print(f"Stratégie {self.strategy_count} terminée (Score cumulé 3 runs: {self.strategy_total_score:.2f})")
                    
                    
                    if self.strategy_total_score > self.bestScore:
                        print(f"--> NOUVEAU RECORD ! (Ancien: {self.bestScore:.2f})")
                        self.bestVec = self.param[:] 
                        self.bestScore = self.strategy_total_score
                    
                    
                    self.strategy_count += 1
                    
                    if self.strategy_count < self.max_strategies:
                        
                        self.param = [random.randint(-1, 1) for i in range(8)]
                        print(f"Test de la stratégie n°{self.strategy_count}")
                    else:
                        
                        print("*** FIN DE LA RECHERCHE - MODE DÉMONSTRATION ***")
                        self.param = self.bestVec[:] 
                
         
                self.run_count = 0
                self.strategy_total_score = 0
                
                return 0, 0, True 


        translation = math.tanh(self.param[0] + 
                                self.param[1] * sensors[sensor_front_left] + 
                                self.param[2] * sensors[sensor_front] + 
                                self.param[3] * sensors[sensor_front_right])
        
        rotation = math.tanh(self.param[4] + 
                             self.param[5] * sensors[sensor_front_left] + 
                             self.param[6] * sensors[sensor_front] + 
                             self.param[7] * sensors[sensor_front_right])

        self.iteration += 1        

        return translation, rotation, False