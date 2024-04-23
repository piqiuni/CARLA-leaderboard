from leaderboard.autoagents.ros1_agent import ROS1Agent
from leaderboard.autoagents.autonomous_agent import AutonomousAgent, Track


## (Ref)[https://leaderboard.carla.org/get_started/#3-creating-your-own-autonomous-agent]

## Vehicle controls
# Vehicle controls must be published to a ROS topic named /carla/hero/vehicle_control_cmd 
# (carla_msgs/CarlaEgoVehicleControl)[https://github.com/carla-simulator/ros-carla-msgs/blob/leaderboard-2.0/msg/CarlaEgoVehicleControl.msg]. 
# Make sure to fill the header of the message with the correspoding timestamp.

## Sensor
# Sensor data is also available through ROS topics. The topic name is structured as follows: /carla/hero/<sensor-id>. 
# For a complete reference check the CARLA ROS sensor documentation[https://carla.readthedocs.io/projects/ros-bridge/en/latest/ros_sensors/].

## Ego vehicle route. 
# The route is published in the following topics:
# /carla/hero/global_plan (carla_msgs/CarlaRoute)
# /carla/hero/global_plan_gnss (carla_msgs/CarlaGnnsRoute)

## Init
# Additionally, ROS-based agents must communicate to the Leadeboard when the stack initialization is finished. 
# This communication should be done by publishing in the following topic /carla/hero/status std_msgs/Bool.



def get_entry_point():
    return 'DemoAgent'

class DemoAgent(ROS1Agent):
    def setup(self, path_to_conf_file):
        self.track = Track.SENSORS
        
    def sensors(self):
        """
        Define the sensor suite required by the agent

        :return: a list containing the required sensors in the following format:

        [
            {'type': 'sensor.camera.rgb', 'x': 0.7, 'y': -0.4, 'z': 1.60, 'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0,
                      'width': 300, 'height': 200, 'fov': 100, 'id': 'Left'},

            {'type': 'sensor.camera.rgb', 'x': 0.7, 'y': 0.4, 'z': 1.60, 'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0,
                      'width': 300, 'height': 200, 'fov': 100, 'id': 'Right'},

            {'type': 'sensor.lidar.ray_cast', 'x': 0.7, 'y': 0.0, 'z': 1.60, 'yaw': 0.0, 'pitch': 0.0, 'roll': 0.0,
             'id': 'LIDAR'}
        ]
        """

        sensors = [
            {'type': 'sensor.camera.rgb', 'x': 0.7, 'y': 0.0, 'z': 1.60, 'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0,
             'width': 1280, 'height': 720, 'fov': 100, 'id': 'Center'},
        ]
        return sensors
    
    def get_ros_entry_point(self):
        return {
            "package": "my_ros_agent",
            "launch_file": "my_ros_agent.launch",
            "parameters": {}
        }
        
        