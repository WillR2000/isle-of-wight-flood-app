import os
import sys
import networkx as nx
from rtree import index
import json
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from shapely.geometry import Point, LineString
import tkinter.messagebox


class UserInput:
    def __init__(self, easting, northing, folder):
        self.easting = easting
        self.northing = northing
        self.folder = folder

    # Create a location point and test if the user is within elevation bounds, else quit the application.
    def location(self):
        location = Point(self.easting, self.northing)
        isle_of_wight = gpd.read_file(self.folder + '/shape/isle_of_wight.shp')
        p_i_p = isle_of_wight.intersects(location)

        if 430000 <= self.easting <= 465000 and 80000 <= self.northing <= 95000:
            if p_i_p[0]:
                ''
            else:
                tkinter.messagebox.showwarning('Warning', 'Error! Swim to shore or call 999 and ask for the coastguard')
                raise Exception('Please input a location on land')

        # Extend the region to the elevation raster bounds and test if the location is within the Isle of Wight.
        elif 425000 <= self.easting <= 470000 and 75000 <= self.northing <= 100000:
            if p_i_p[0]:
                ''
            else:
                tkinter.messagebox.showwarning('Warning', 'Error! Swim to shore or call 999 and ask for the coastguard')
                raise Exception('Please input a coordinate on land')
        else:
            tkinter.messagebox.showwarning('Warning', 'Error! You are not on or near the Isle of Wight')
            raise sys.exit()

        return location


class Transform:
    def __init__(self, user_location, folder):
        self.user_location = user_location
        self.folder = folder

    def get_transform(self):
        # Create a GeoDataFrame of the 5km buffer and export as a json file for masking.
        scope_buffer = gpd.GeoDataFrame({'geometry': self.user_location.buffer(5000)}, index=[0], crs='EPSG:27700')
        clip_range = [json.loads(scope_buffer.to_json())['features'][0]['geometry']]

        # Use the buffer to clip the elevation array.
        elevation = rasterio.open(self.folder + '/elevation/SZ.asc')
        out_image_h, out_transform_h = rasterio.mask.mask(elevation, clip_range, crop=False)
        out_meta_h = elevation.meta.copy()
        out_meta_h.update({"driver": "GTiff", "height": out_image_h.shape[1], "width": out_image_h.shape[2],
                           "transform": out_transform_h})

        # Set the path of the new clipped elevation and export.
        out_tif_h = self.folder + '/elevation/out.tif'
        with rasterio.open(out_tif_h, 'w', **out_meta_h) as output:
            output.write(out_image_h)

        return out_transform_h


class HighestPoint:
    def __init__(self, transform, buffer, folder):
        self.transform = transform
        self.buffer = buffer
        self.folder = folder

    def find_highest_point(self):
        # Use numpy to find the array position of the highest elevation, and convert to easting and northing.
        out_tif_h = rasterio.open(self.folder + '/elevation/out.tif')
        search_area = out_tif_h.read(1)
        highest_elevation = np.amax(search_area)
        matrix_position = np.where(search_area == highest_elevation)
        highest_point_x = matrix_position[0][0]
        highest_point_y = matrix_position[1][0]
        highest_easting, highest_northing = rasterio.transform.xy(self.transform, highest_point_x, highest_point_y)

        destination = Point(highest_easting, highest_northing)

        # Check destination point is within the 5km buffer.
        bounds = self.buffer.bounds
        if bounds[0] <= highest_easting <= bounds[2] and bounds[1] <= highest_northing <= bounds[3]:
            return destination

        else:
            raise Exception('Error: Destination is beyond the 5km boundary')


class NearestItn:
    def __init__(self, location, destination, buffer, folder):
        self.location = location
        self.destination = destination
        self.buffer = buffer
        self.folder = folder

    def nearest_itn(self):
        # join path components and read itn file.
        isle_of_wight_itn_json = os.path.join(self.folder + '/itn', 'solent_itn.json')
        with open(isle_of_wight_itn_json, "r") as f:
            isle_of_wight_itn = json.load(f)

        # Create a list of road node coordinates and insert them into a spatial index if they intersect the 5km buffer.
        road_nodes = isle_of_wight_itn['roadnodes']
        node_points = []
        for node in road_nodes:
            node_points.append(road_nodes[node]['coords'])

        idx = index.Index()
        for n, point in enumerate(node_points):
            p = Point(point)
            if p.intersects(self.buffer):
                idx.insert(n, point, str(n))

        # Define queries by getting x and y attributes of user location point and highest point.
        q_start = (getattr(self.location, 'x'), getattr(self.location, 'y'))
        q_end = (getattr(self.destination, 'x'), getattr(self.destination, 'y'))

        # Perform a nearest neighbour search.
        start_node_id = list(idx.nearest(q_start, 1))
        s = int(start_node_id[0])
        start_coordinates = node_points[s]

        end_node_id = list(idx.nearest(q_end, 1))
        e = int(end_node_id[0])
        end_coordinates = node_points[e]

        # Find the nearest start and end road node id to the user input and highest point, respectively.
        road_links = isle_of_wight_itn['roadlinks']
        start = ''
        for link in road_links:
            road_coordinates = road_links[link]['coords']
            for coordinate in road_coordinates:
                if coordinate == start_coordinates[0:2]:
                    start = str(road_links[link]['start'])

        end = ''
        for link in road_links:
            road_coordinates = road_links[link]['coords']
            for coordinate in road_coordinates:
                if coordinate == end_coordinates[0:2]:
                    end = str(road_links[link]['end'])

        return start, end


class ShortestPath:
    def __init__(self, start_point, end_point, buffer, transform, folder):
        self.start_point = start_point
        self.end_point = end_point
        self.buffer = buffer
        self.transform = transform
        self.folder = folder

    def shortest_path(self):
        # join path components and read itn file.
        isle_of_wight_itn_json = os.path.join(self.folder + '/itn', 'solent_itn.json')
        with open(isle_of_wight_itn_json, 'r') as f:
            isle_of_wight_itn = json.load(f)

        # Calculate the time weight of each link segment using Naismith's rule and create a graph.
        g = nx.DiGraph()
        road_links = isle_of_wight_itn['roadlinks']
        elevation = rasterio.open(self.folder + '/elevation/SZ.asc')
        elevation_array = elevation.read(1)
        time = []

        for link in road_links:
            road_length = road_links[link]['length']
            road_coordinates = road_links[link]['coords']
            line = LineString(road_coordinates)

            # if link is in the 5km buffer.
            if line.within(self.buffer) or line.touches(self.buffer):
                # time(s) = distance(m) / speed(m/s)
                walking_time = road_length / (5000 / 3600)

                count = 0
                elevation_values = []
                for point in enumerate(road_coordinates):
                    point = point[1]
                    matrix_position = rasterio.transform.rowcol(self.transform, point[0], point[1])
                    elevation = elevation_array[matrix_position[0]][matrix_position[1]]
                    elevation_values.append(elevation)

                point_1_elevation = elevation_values[0]
                for i in range(len(elevation_values)):
                    if i != 0:
                        point_2_elevation = elevation_values[i]
                        if point_2_elevation > point_1_elevation:
                            count += point_2_elevation - point_1_elevation
                        point_1_elevation = point_2_elevation

                ascending_time_forwards = count / (10 / 60)
                time_forwards = walking_time + ascending_time_forwards
                g.add_edge(road_links[link]['start'], road_links[link]['end'], fid=link, weight=time_forwards)
                time.append([road_links[link]['start'], road_links[link]['end'], time_forwards])

                count = 0
                elevation_values = []
                for point in enumerate(reversed(road_coordinates)):
                    point = point[1]
                    matrix_position = rasterio.transform.rowcol(self.transform, point[0], point[1])
                    elevation = elevation_array[matrix_position[0]][matrix_position[1]]
                    elevation_values.append(elevation)

                point_1_elevation = elevation_values[0]
                for i in range(len(elevation_values)):
                    if i != 0:
                        point_2_elevation = elevation_values[i]
                        if point_2_elevation > point_1_elevation:
                            count += point_2_elevation - point_1_elevation
                        point_1_elevation = point_2_elevation

                ascending_time_backwards = count / (10 / 60)
                time_backwards = walking_time + ascending_time_backwards
                g.add_edge(road_links[link]['end'], road_links[link]['start'], fid=link, weight=time_backwards)
                time.append([road_links[link]['end'], road_links[link]['start'], time_backwards])

        # Find the shortest path between the nearest user ITN (start) and nearest highest point ITN (end).
        start = self.start_point
        end = self.end_point
        path = nx.dijkstra_path(g, source=start, target=end, weight='weight')
        
        # Find the time (s) spent on the shortest path
        min_time = 0
        for i in range(len(time)):
            min_time = time[0][2]
            if i != 0 and time[i][2] < min_time:
                min_time = time[i][2]

        # Create GeoDataframe of shortest path.
        links = []
        geom = []
        first_node = path[0]
        for node in path[1:]:
            link_fid = g.edges[first_node, node]['fid']
            links.append(link_fid)
            geom.append(LineString(road_links[link_fid]['coords']))
            first_node = node

        shortest_path_gpd = gpd.GeoDataFrame({'fid': links, 'geometry': geom})

        return shortest_path_gpd, min_time
