import pickle
import carla
from leaderboard.autoagents.autonomous_agent import AutonomousAgent, Track
from srunner.scenariomanager.timer import GameTime
from leaderboard.utils.route_manipulation import downsample_route
from leaderboard.envs.sensor_interface import SensorInterface


def get_entry_point():
    return "MyAgent"


class MyAgent(AutonomousAgent):
    def __init__(self, carla_host, carla_port, debug=False):
        super().__init__(carla_host, carla_port, debug)

    def setup(self, path_to_conf_file):
        """
        Initialize everything needed by your agent and set the track attribute to the right type:
            Track.SENSORS : CAMERAS, LIDAR, RADAR, GPS and IMU sensors are allowed
            Track.MAP : OpenDRIVE map is also allowed
        """
        self.track = Track.SENSORS
        pass

    def sensors(self):  # pylint: disable=no-self-use
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
            {
                "type": "sensor.camera.rgb",
                "id": "Front",
                "x": 0.005060318644935326,
                "y": 1.5205331732469152,
                "z": -1.6923035337063868,
                "roll": 2.3527706379648343,
                "pitch": -1.5627907131441763,
                "yaw": -0.7811531953358893,
                "width": 300,
                "height": 200,
                "fov": 100,
            },
            {
                "type": "sensor.camera.rgb",
                "x": 1.0322882942430183,
                "y": 1.5036442540372867,
                "z": -1.2487090915837091,
                "roll": -1.587182466720529,
                "pitch": -0.5864155802844836,
                "yaw": -3.1415807215081353,
                "width": 300,
                "height": 200,
                "fov": 100,
                "id": "FrontRight",
            },
            {
                "type": "sensor.camera.rgb",
                "x": -0.964967792249035,
                "y": 1.5082481835748522,
                "z": -1.2802190054327949,
                "roll": 1.5678144751007432,
                "pitch": -0.6080589788270796,
                "yaw": -0.0004160109906855529,
                "width": 300,
                "height": 200,
                "fov": 100,
                "id": "FrontLeft",
            },
            {
                "type": "sensor.camera.rgb",
                "x": 0.00279684819674121,
                "y": 1.5793576699533447,
                "z": 0.0018731325118756781,
                "roll": 0.14753406074399214,
                "pitch": 1.5538677970085022,
                "yaw": -1.4272422517097234,
                "width": 300,
                "height": 200,
                "fov": 100,
                "id": "Back",
            },
            {
                "type": "sensor.camera.rgb",
                "x": 1.1362025694795879,
                "y": 1.5514497761330326,
                "z": -0.06364231814995075,
                "roll": -1.5881956511907303,
                "pitch": 0.3627899776279022,
                "yaw": 3.1246106940695095,
                "width": 300,
                "height": 200,
                "fov": 100,
                "id": "BackRight",
            },
            {
                "type": "sensor.camera.rgb",
                "x": -1.1421927830307241,
                "y": 1.588555678583558,
                "z": -0.103705227081661,
                "roll": 1.5876890982006504,
                "pitch": 0.3245322804194959,
                "yaw": 0.009143105555921743,
                "width": 300,
                "height": 200,
                "fov": 100,
                "id": "BackLeft",
            },
            {
                "type": "sensor.lidar.ray_cast",
                "id": "LIDAR",
                "x": 0.008937887797948386,
                "y": -0.8988461327047562,
                "z": -1.86253489228347,
                "roll": -0.005850392818186975,
                "pitch": -0.0242440962144983,
                "yaw": 1.5687624763201402,
            },
            # {'type': 'sensor.other.radar', 'id': 'RADAR',
            # 'x': 0.7, 'y': -0.4, 'z': 1.60, 'roll': 0.0, 'pitch': 0.0, 'yaw': -45.0, 'fov': 30},
            {"type": "sensor.other.gnss", "id": "GPS", "x": 0.7, "y": -0.4, "z": 1.60},
            {"type": "sensor.other.imu", "id": "IMU", "x": 0.7, "y": -0.4, "z": 1.60},
            # {'type': 'sensor.opendrive_map', 'id': 'OpenDRIVE', 'reading_frequency': 1},
            {"type": "sensor.speedometer", "id": "Speed"},
        ]

        return sensors

    def run_step(self, input_data, timestamp):
        """
        Execute one step of navigation.
        :return: control
        """
        control = carla.VehicleControl()
        control.steer = 0.0
        control.throttle = 0.0
        control.brake = 0.0
        control.hand_brake = False

        print(type(input_data))
        print("---------------------")

        pickle.dump(input_data, open("input_data.pkl", "wb"))
        return control

    def destroy(self):
        """
        Destroy (clean-up) the agent
        :return:
        """
        pass

    def __call__(self):
        """
        Execute the agent call, e.g. agent()
        Returns the next vehicle controls
        """
        input_data = self.sensor_interface.get_data(GameTime.get_frame())

        timestamp = GameTime.get_time()

        if not self.wallclock_t0:
            self.wallclock_t0 = GameTime.get_wallclocktime()
        wallclock = GameTime.get_wallclocktime()
        wallclock_diff = (wallclock - self.wallclock_t0).total_seconds()
        sim_ratio = 0 if wallclock_diff == 0 else timestamp / wallclock_diff

        print(
            "=== [Agent] -- Wallclock = {} -- System time = {} -- Game time = {} -- Ratio = {}x".format(
                str(wallclock)[:-3],
                format(wallclock_diff, ".3f"),
                format(timestamp, ".3f"),
                format(sim_ratio, ".3f"),
            )
        )

        control = self.run_step(input_data, timestamp)
        control.manual_gear_shift = False

        return control

    @staticmethod
    def get_ros_version():
        return -1

    def set_global_plan(self, global_plan_gps, global_plan_world_coord):
        """
        Set the plan (route) for the agent
        """
        ds_ids = downsample_route(global_plan_world_coord, 200)
        self._global_plan_world_coord = [
            (global_plan_world_coord[x][0], global_plan_world_coord[x][1])
            for x in ds_ids
        ]
        self._global_plan = [global_plan_gps[x] for x in ds_ids]
