from robot import *
import math
import random 
nb_robots = 0
debug = False

class Robot_player(Robot):

    team_name = "Optimizer"
    robot_id = -1
    iteration = 0

    param = []
    bestVec = []
    it_per_evaluation = 400
    trial = 0

    x_0 = 0
    y_0 = 0
    theta_0 = 0 

    def __init__(self, x_0, y_0, theta_0, name="n/a", team="n/a",evaluations=0,it_per_evaluation=0):
        global nb_robots
        self.robot_id = nb_robots
        nb_robots+=1
        self.x_0 = x_0
        self.y_0 = y_0
        self.theta_0 = theta_0
        self.param = [random.randint(-1, 1) for i in range(18)]
        self.it_per_evaluation = 400
        super().__init__(x_0, y_0, theta_0, name=name, team=team)
        self.current_score = 0
        self.steps=0
        self.score=0
        self.evaluations=evaluations
        self.bestScore = -1000
        self.bestVec = self.param[:]
        self.last_x,self.last_y,self.last_theta = x_0,y_0,theta_0

    def reset(self):
        super().reset()

    def step(self, sensors, sensor_view=None, sensor_robot=None, sensor_team=None):
        dist_reelle = math.sqrt((self.x - self.last_x)**2 + (self.y - self.last_y)**2)
        rot_reelle = abs(self.theta - self.last_theta)
        
        self.last_x = self.x
        self.last_y = self.y
        self.last_theta = self.theta

        step_score = dist_reelle * abs(1 - rot_reelle)
        self.current_score += step_score

        if self.iteration >= self.it_per_evaluation:
            
            if self.current_score > self.bestScore:
                print(f"--> NEW RECORD! Old: {self.bestScore} -> New: {self.current_score}")
                self.bestVec = self.param[:] 
                self.bestScore = self.current_score
        


            self.trial += 1
            print(f"End of trial {self.trial} (Score: {self.current_score})")

            if self.trial < self.evaluations:
                n=random.randint(0,17)
                choix_possibles = [-1, 0, 1]
                

                valeur_actuelle = self.param[n]
                if valeur_actuelle in choix_possibles:
                    choix_possibles.remove(valeur_actuelle)
                
                self.param[n] = random.choice(choix_possibles)
                self.param = self.bestVec[:]

                print(f"Trying strategy no. {self.trial + 1}")
            else:
                self.param = self.bestVec[:]
                self.it_per_evaluation = 1000
                print("*** REPLAYING BEST STRATEGY ***")

            self.current_score = 0 
            self.iteration = 0
            self.last_x, self.last_y = self.x_0, self.y_0
            
            return 0, 0, True 

        translation = math.tanh ( self.param[0] + self.param[1] * sensors[sensor_front_left] + self.param[2] * sensors[sensor_front] +
        self.param[3] * sensors[sensor_front_right] + self.param[4] * sensors[sensor_right] + self.param[5] * sensors[sensor_rear_right] 
        +self.param[6] * sensors[sensor_rear] +self.param[7] * sensors[sensor_rear_left] +self.param[8] * sensors[sensor_left] )
        
        rotation =  math.tanh ( self.param[9] + self.param[10] * sensors[sensor_front_left] + self.param[11] * sensors[sensor_front] +
        self.param[12] * sensors[sensor_front_right] + self.param[13] * sensors[sensor_right] + self.param[14] * sensors[sensor_rear_right] 
        +self.param[15] * sensors[sensor_rear] +self.param[16] * sensors[sensor_rear_left] +self.param[17] * sensors[sensor_left] )

        if debug == True:
            if self.iteration % 100 == 0:
                print ("Robot",self.robot_id," (team "+str(self.team_name)+")","at step",self.iteration,":")
                print ("\tsensors (distance, max is 1.0)  =",sensors)
                print ("\ttype (0:empty, 1:wall, 2:robot) =",sensor_view)
                print ("\trobot's name (if relevant)      =",sensor_robot)
                print ("\trobot's team (if relevant)      =",sensor_team)

        self.iteration = self.iteration + 1        

        return translation, rotation, False