import os
from classes import UserInput, NearestItn, HighestPoint, ShortestPath, Transform
from plotter import Plotter


def main():
    # Test if the user input is within the Isle of Wight, returning the user location as a point.
    print('User Input')
    easting = int(input('Please input your current British National Grid Easting coordinate: '))
    northing = int(input('Please input your current British National Grid Northing coordinate: '))
    user_loc = UserInput(easting, northing).location()
    buffer = user_loc.buffer(5000)

    # Identify the highest point of land within a 5km radius of the user location.
    print('Highest Point')
    out_transform = Transform(user_loc).get_transform()
    destination = HighestPoint(out_transform, buffer).find_highest_point()

    # Identify the nearest Integrated Transport Network (ITN) node to the user and to the highest point.
    print('Nearest Integrated Transport Network')
    start, end = NearestItn(user_loc, destination, buffer).nearest_itn()

    # Identify the shortest route between the user location and highest point using Naismith's rule.
    print('Shortest Path')
    shortest_path = ShortestPath(start, end, buffer, out_transform).shortest_path()

    # Plot all components for the user.
    print('Map Plotting')
    map_background = os.path.join('background', 'raster-50k_2724246.tif')
    Plotter(map_background, user_loc, destination, shortest_path).plot_graph()


if __name__ == '__main__':
    main()
