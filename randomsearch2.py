
from robot import * 
import math

nb_robots = 0
debug = False

class Robot_player(Robot):

    team_name = "Optimizer"
    robot_id = -1
    iteration = 0

    param = []
    bestParam = []
    it_per_evaluation = 400
    trial = 0

    x_0 = 0
    y_0 = 0
    theta_0 = 0 # in [0,360]

    def __init__(self, x_0, y_0, theta_0, name="n/a", team="n/a",evaluations=500,it_per_evaluation=400):
        global nb_robots
        self.robot_id = nb_robots
        nb_robots+=1
        self.x_0 = x_0
        self.y_0 = y_0
        self.theta_0 = theta_0
        self.param = [random.randint(-1, 1) for i in range(18)]
        self.it_per_evaluation = it_per_evaluation
        super().__init__(x_0, y_0, theta_0, name=name, team=team)
        self.round=self.it_per_evaluation //3
        self.bestParam = self.param
        self.score = 0
        self.last_x,self.last_y,self.last_theta = x_0,y_0,theta_0
        self.current_score = 0
        self.evaluations = evaluations
        self.bestScore = 0



    def reset(self):
        self.x = random.randint (0, 100)
        self.x = random.randint (0, 100)
        self.theta = random.random()*360
        self.log_sum_of_translation = 0
        self.log_sum_of_rotation = 0

    def step(self, sensors, sensor_view=None, sensor_robot=None, sensor_team=None):

        # cet exemple montre comment générer au hasard, et évaluer, des stratégies comportementales
        # Remarques:
        # - la liste "param", définie ci-dessus, permet de stocker les paramètres de la fonction de contrôle
        # - la fonction de controle est une combinaison linéaire des senseurs, pondérés par les paramètres (c'est un "Perceptron")

        # toutes les X itérations: le robot est remis à sa position initiale de l'arène avec une orientation aléatoire

        dist_reelle = math.sqrt((self.x - self.last_x)**2 + (self.y - self.last_y)**2)
        rot_reelle = abs(self.theta - self.last_theta)
        
        self.last_x = self.x
        self.last_y = self.y
        self.last_theta = self.theta

        step_score = dist_reelle * abs(1 - rot_reelle)
        self.current_score += step_score
        if self.iteration % self.it_per_evaluation == 0:
            
                if self.iteration % self.round == 0:
                    self.reset()

                if self.iteration > 0:
                    print ("\tparameters           =",self.param)
                    print ("\ttranslations         =",self.log_sum_of_translation,"; rotations =",self.log_sum_of_rotation) # *effective* translation/rotation (ie. measured from displacement)
                    print ("\tdistance from origin =",math.sqrt((self.x-self.x_0)**2+(self.y-self.y_0)**2))
                if self.current_score > self.bestScore:
                    print(f"--> NEW RECORD! Old: {self.bestScore} -> New: {self.current_score}")
                    self.bestVec = self.param[:] 
                    self.bestScore = self.current_score

                self.trial += 1
                print(f"End of trial {self.trial} (Score: {self.current_score})")

                if self.trial < self.evaluations:
                    self.param = [random.randint(-1, 1) for i in range(18)]
                    print(f"Trying strategy no. {self.trial + 1}")
                else:
                    self.param = self.bestVec[:]
                    self.it_per_evaluation = 1000
                    print("*** REPLAYING BEST STRATEGY ***")

                self.current_score = 0 
                self.iteration = 0
                self.last_x, self.last_y = self.x_0, self.y_0

                print ("Trying strategy no.",self.trial)
                self.iteration = self.iteration + 1
                return 0, 0, True # ask for reset

        # fonction de contrôle (qui dépend des entrées sensorielles, et des paramètres)
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
