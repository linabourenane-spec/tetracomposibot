
from robot import * 

nb_robots = 0
debug = True

class Robot_player(Robot):

    team_name = "subsomption"
    robot_id = -1
    iteration = 0

    def __init__(self, x_0, y_0, theta_0, name="n/a", team="n/a"):
        global nb_robots
        self.robot_id = nb_robots
        nb_robots+=1
        super().__init__(x_0, y_0, theta_0, name=name, team=team)

    def hatewall(self, sensors, sensor_view):

        sensor_to_wall = []

        for i in range (0,8):
            if  sensor_view[i] == 1:
                sensor_to_wall.append( sensors[i] )

            elif  sensor_view[i] == 2:
                sensor_to_wall.append( 1.0 )

            else:
                sensor_to_wall.append(1.0)

        
        if sensors[sensor_front] < 0.6 or sensors[sensor_front_left] < 0.6 or sensors[sensor_front_right] < 0.6:
            translation = 0.2

            rotation =  (sensors[sensor_rear_left]-sensor_to_wall[sensor_front_left])*(-1)+(sensors[sensor_rear_left]-sensor_to_wall[sensor_front_right])+(sensors[sensor_rear_left]-sensor_to_wall[sensor_front])

            return translation, rotation, True 
        return 0, 0, False
    
    def lovebot(self, sensors, sensor_robot):
         
        if sensor_robot[sensor_front] < 0.9 or sensor_robot[sensor_front_left] < 0.8 or sensor_robot[sensor_front_right] < 0.8:
                translation = 1.0
                rotation = (sensors[sensor_rear_left]-sensor_robot[sensor_front_left])+(sensors[sensor_rear_left]-sensor_robot[sensor_front_right])*(-1)-(sensors[sensor_rear_left]-sensor_robot[sensor_front])
                return translation, rotation, True
        return 0, 0, False
    
    def go_straight(self):

        return 1, 0.0, True 

    def step(self, sensors, sensor_view=None, sensor_robot=None, sensor_team=None):

        sensor_to_wall = []
        sensor_to_robot = []
        for i in range (0,8):
            if  sensor_view[i] == 1:
                sensor_to_wall.append( sensors[i] )
                sensor_to_robot.append(1.0)
            elif  sensor_view[i] == 2:
                sensor_to_wall.append( 1.0 )
                sensor_to_robot.append( sensors[i] )
            else:
                sensor_to_wall.append(1.0)
                sensor_to_robot.append(1.0)

        if debug == True:
            if self.iteration % 100 == 0:
                print ("Robot",self.robot_id," (team "+str(self.team_name)+")","at step",self.iteration,":")
                print ("\tsensors (distance, max is 1.0)  =",sensors)
                print ("\t\tsensors to wall  =",sensor_to_wall)
                print ("\t\tsensors to robot =",sensor_to_robot)
                print ("\ttype (0:empty, 1:wall, 2:robot) =",sensor_view)
                print ("\trobot's name (if relevant)      =",sensor_robot)
                print ("\trobot's team (if relevant)      =",sensor_team)


        self.iteration = self.iteration + 1
        r,w,b=self.hatewall(sensors, sensor_view)
        print(sensors[sensor_front])
        if b==True:
            print(r,w,b)
            return r,w,False
        r,w,b=self.lovebot(sensors, sensor_view)
        
        if b==True:
            print("Love Bot activated")
            return r,w,False
        r,w,b=self.go_straight()
        if b==True:
            print("Go Straight activated")
            return r,w,False    

