#!/usr/bin/env python

# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
This module provides an NPC agent to control the ego vehicle
"""

from __future__ import print_function

import time
import carla
import numpy as np
import math
import os
import xml.etree.ElementTree as ET
from leaderboard.autoagents.map_agent_controller import VehiclePIDController
from leaderboard.autoagents.autonomous_agent import AutonomousAgent, Track

import ad_map_access as ad

def get_entry_point():
    return 'MapAgent'

class MapAgent(AutonomousAgent):
    """Autonomous agent to control the ego vehicle using the AD Map library
    to parse the opendrive map information"""

    def setup(self, path_to_conf_file):
        """
        Setup the agent parameters
        """
        self.track = Track.MAP

        # Route
        self._route = []
        self._route_assigned = False

        # Controller
        self._controller = None
        self._prev_location = None
        self._args_lateral_pid = {'K_P': 1.95, 'K_D': 0.2, 'K_I': 0.07, 'dt': 0.05}
        self._args_longitudinal_pid = {'K_P': 1.0, 'K_D': 0, 'K_I': 0.05, 'dt': 0.05}

        self._route_index = 0
        self._route_index_buffer = 5
        self._added_target_index = 5  # This will mean the waypoint is at x*resolution meters

        # AD map library
        self._map_initialized = False
        self._map_name = 'LeaderboardMap'

        # Debugging, remove afterwards
        self.client = carla.Client('127.0.0.1', 2000)
        self.client.set_timeout(5.0)
        self.world = self.client.get_world()
        self._vehicle = None

    def sensors(self):
        """
        Define the sensor suite required by the agent
        """
        sensors = [
            {'type': 'sensor.opendrive_map', 'id': 'ODM', 'reading_frequency': 1},
            {'type': 'sensor.speedometer', 'id': 'Speed'},
            {'type': 'sensor.other.gnss', 'x': 0, 'y': 0, 'z': 0, 'id': 'GNSS'},
        ]

        return sensors

    def run_step(self, input_data, timestamp):
        """
        Execute one step of navigation.
        """
        control = carla.VehicleControl()

        # Initialize the map library
        if not self._map_initialized:
            if 'ODM' in input_data:
                self._initialize_map(input_data['ODM'][1]['opendrive'])
                self._map_initialized = True
            else:
                return control

        # Find the vehicle agent
        if not self._vehicle:
            self._find_vehicle()

        # Create the route
        if not self._route:
            self._populate_route()

        # Create the controller, or run it one step
        if not self._controller:
            self._controller = VehiclePIDController(self._args_lateral_pid, self._args_longitudinal_pid)
        else:
            # Longitudinal PID values
            target_speed = 30
            current_speed = self._get_current_speed(input_data)

            # Lateral PID values
            current_location = self._get_current_location(input_data)
            # self.world.debug.draw_point(current_location + carla.Location(z=1.5), life_time=0.1, color=carla.Color(255, 0, 0), size=0.2)

            if self._vehicle:
                current_heading = self._vehicle.get_transform().get_forward_vector()
            elif self._prev_location is None:
                current_heading = carla.Vector3D()
            else:
                current_heading = current_location - self._prev_location
            # print(math.atan2(current_heading.y, current_heading.x) / math.pi * 180)

            target_location = self._get_target_location(current_location)
            # self.world.debug.draw_point(target_location + carla.Location(z=1.5), life_time=0.15, color=carla.Color(0, 0, 0), size=0.1)

            control = self._controller.run_step(
                target_speed, current_speed,
                target_location, current_location, current_heading
            )

            self._prev_location = current_location

        return control

    def _initialize_map(self, opendrive_contents):
        """
        Initialize the AD map library and, creates the file needed to do so.
        """
        lat_ref = 0.0
        lon_ref = 0.0

        with open(self._map_name + '.xodr', 'w') as f:
            f.write(opendrive_contents)

        # Get geo reference
        xml_tree = ET.parse(self._map_name + '.xodr')
        for geo_elem in xml_tree.find('header').find('geoReference').text.split(' '):
            if geo_elem.startswith('+lat_0'):
                lat_ref = float(geo_elem.split('=')[-1])
            elif geo_elem.startswith('+lon_0'):
                lon_ref = float(geo_elem.split('=')[-1])

        with open(self._map_name + '.txt', 'w') as f:
            txt_content = "[ADMap]\n" \
                          "map=" + self._map_name + ".xodr\n" \
                          "[ENUReference]\n" \
                          "default=" + str(lat_ref) + " " + str(lon_ref) + " 0.0"
            f.write(txt_content)

        assert ad.map.access.init(self._map_name + '.txt')

    def _find_vehicle(self):
        vehicles = self.world.get_actors().filter('*vehicle*')
        for vehicle in vehicles:
            if vehicle.attributes['role_name'] == "hero":
                self._vehicle = vehicle
                break

    def _populate_route(self, resolution=1):
        """
        This method uses the ad map library to create a more dense route
        with waypoints every 'resolution' meters.
        """

        for i in range (1, len(self._global_plan_world_coord)):

            # Get the stating and end location of the route segment
            start_location = self._global_plan_world_coord[i-1][0].location
            end_location = self._global_plan_world_coord[i][0].location

            # self.world.debug.draw_point(start_location + carla.Location(z=1), life_time=200, color=carla.Color(255, 255, 0), size=0.1)
            # self.world.debug.draw_point(end_location + carla.Location(z=1.5), life_time=200, color=carla.Color(0, 255, 255), size=0.1)

            # Get the route and increase the number of waypoints of the rotue
            routeResult = ad.map.route.planRoute(
                ad.map.route.createRoutingPoint(self._to_ad_paraPoint(start_location)),
                ad.map.route.createRoutingPoint(self._to_ad_paraPoint(end_location))
            )

            # Increases the density of the waypoints
            for road_segment in routeResult.roadSegments:
                for lane_segment in road_segment.drivableLaneSegments:

                    # Get the list of params that separate the route in meters of size 'resolution'
                    start = float(lane_segment.laneInterval.start)
                    end = float(lane_segment.laneInterval.end)
                    length = float(ad.map.lane.calcLength(lane_segment.laneInterval.laneId))
                    param_list = np.arange(start, end, np.sign(end - start) * resolution / length)

                    for param in param_list:
                        para_point = ad.map.point.createParaPoint(
                            lane_segment.laneInterval.laneId,
                            ad.physics.ParametricValue(param)
                        )

                        enu_point = ad.map.lane.getENULanePoint(para_point)
                        carla_location = carla.Location(float(enu_point.x), float(-enu_point.y), float(enu_point.z))
                        self._route.append(carla_location)

    def _to_ad_paraPoint(self, location, distance=1, probability=0):
        """
        Transforms a carla.Location into an ad.map.point.ParaPoint()
        """
        # Get possible matchings
        mapMatching = ad.map.match.AdMapMatching()
        match_results = mapMatching.getMapMatchedPositions(
            ad.map.point.createENUPoint(location.x, -location.y, location.z),
            ad.physics.Distance(distance),
            ad.physics.Probability(probability)
        )

        if not match_results:
            raise ValueError("Couldn't find a para point for CARLA location {}. Consider "
                             "increasing the distance or reducing the probability".format(location))

        # Filter the closest one to the given location
        distance = [float(mmap.matchedPointDistance) for mmap in match_results]
        return match_results[distance.index(min(distance))].lanePoint.paraPoint

    def _get_current_speed(self, sensor_data):
        """Calculates the speed of the vehicle"""
        return 3.6 * sensor_data['Speed'][1]['speed']

    def _get_current_location(self, sensor_data):
        """Calculates the transform of the vehicle"""
        R = 6378135
        lat_rad = (np.deg2rad(sensor_data['GNSS'][1][0]) + np.pi) % (2 * np.pi) - np.pi
        lon_rad = (np.deg2rad(sensor_data['GNSS'][1][1]) + np.pi) % (2 * np.pi) - np.pi
        x = R * np.sin(lon_rad) * np.cos(lat_rad) 
        y = R * np.sin(-lat_rad)
        z = sensor_data['GNSS'][1][2]

        return carla.Location(x, y, z)
    
        # TODO: use this one if changed
        # geo_point = ad.map.point.createGeoPoint(
        #     sensor_data['GNSS'][1][1],  # Long
        #     sensor_data['GNSS'][1][0],  # Lat
        #     sensor_data['GNSS'][1][2]   # Alt
        # )
        # enu_point = ad.map.point.toENU(geo_point)
        # return carla.Location(x=float(enu_point.x), y=-float(enu_point.y), z=float(enu_point.z))

    def _get_target_location(self, current_location):
        """Returns a location of the route that is a bit in front of the ego"""

        min_distance = float('inf')
        start_index = self._route_index
        end_index = min(start_index + self._route_index_buffer, len(self._route))

        for i in range(start_index, end_index):
            route_location = self._route[i]
            distance = current_location.distance(route_location)
            if distance < min_distance:
                self._route_index = i
                min_distance = distance

        target_index = min(self._route_index + self._added_target_index, len(self._route) - 1)

        return self._route[target_index]

    def destroy(self):
        """
        Destroy the agent
        """
        if os.path.exists(self._map_name + '.txt'):
            os.remove(self._map_name + '.txt')
        if os.path.exists(self._map_name + '.xodr'):
            os.remove(self._map_name + '.xodr')

        super(MapAgent, self).destroy()