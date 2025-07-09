from flask import Flask, render_template, request
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as mpatches
import matplotlib.path as mpath
import matplotlib
matplotlib.use('Agg') 

app = Flask(__name__)

def distance(house, booth):
    if house is None or booth is None:
        return float('inf') 
    return np.sqrt((house[0] - booth[0]) ** 2 + (house[1] - booth[1]) ** 2)


def astar_path(city, house, booth):
    return nx.astar_path(city, house, booth, heuristic=lambda u, v: distance(u, v))

# CSP Solution using A* Search Algorithm
def place_booths(city_size, distance_constraint, house_locations):
    booths = []
    uncovered_houses = house_locations.copy()
    city = nx.grid_2d_graph(city_size, city_size)
    paths = []  # To store the A* paths

    while uncovered_houses:
        best_booth = None
        max_coverage = 0
        
        # Try placing a booth in every city node
        for x in range(city_size):
            for y in range(city_size):
                booth = (x, y)
                coverage = [house for house in uncovered_houses if distance(house, booth) <= distance_constraint]
                
                if len(coverage) > max_coverage:
                    max_coverage = len(coverage)
                    best_booth = booth

        if best_booth is None:
            # No valid booth found, breaking out of the loop to avoid infinite loop
            print("No suitable booth found. Exiting...")
            break

        booths.append(best_booth)
        for house in uncovered_houses:
            if distance(house, best_booth) <= distance_constraint:
                try:
                    paths.append(astar_path(city, house, best_booth))
                except nx.NetworkXNoPath:
                    print(f"No path found between house {house} and booth {best_booth}")

        # Remove covered houses from the uncovered list
        uncovered_houses = [house for house in uncovered_houses if distance(house, best_booth) > distance_constraint]

    return booths, paths

def visualize(city_size, booths, house_locations, distance_constraint, paths):
    city = nx.grid_2d_graph(city_size, city_size)
    pos = {(x, y): (y, -x) for x, y in city.nodes()} 


    nx.draw(city, pos, node_size=50, node_color='lightblue', with_labels=False)

    nx.draw_networkx_nodes(city, pos, nodelist=house_locations, node_color='red', node_size=100, label="Houses")

    nx.draw_networkx_nodes(city, pos, nodelist=booths, node_color='green', node_size=100, label="Booths")

    ax = plt.gca() 

    # Draw coverage area for each booth, clipped at grid boundaries
    for booth in booths:
        x, y = booth

        # Generate a circle path (full circle)
        circle = mpatches.Circle(pos[booth], distance_constraint, color='green', alpha=0.3, fill=True, linestyle='--', linewidth=1)
        ax.add_patch(circle)

        # Clip the coverage at grid boundaries
        grid_boundary_path = mpath.Path([
            (0, 0),  
            (city_size - 1, 0),  
            (city_size - 1, -(city_size - 1)),  
            (0, -(city_size - 1)),  
            (0, 0)  
        ])
        clip_patch = mpatches.PathPatch(grid_boundary_path, transform=ax.transData)

        # Clip the circle to the grid boundaries
        circle.set_clip_path(clip_patch)

    # Draw A* paths from houses to booths, in bold blue color
    for path in paths:
        path_edges = list(zip(path[:-1], path[1:]))
        nx.draw_networkx_edges(city, pos, edgelist=path_edges, edge_color='blue', width=3) 

    plt.legend(["Houses", "Paths", "Selected Houses"])
    plt.savefig("static/city_map.png")
    plt.close()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        city_size = int(request.form['city_size'])
        distance_constraint = int(request.form['distance_constraint'])
        
        house_locations = [(int(x.split(',')[0]), int(x.split(',')[1])) for x in request.form['houses'].split(';')]

        booths, paths = place_booths(city_size, distance_constraint, house_locations)
        visualize(city_size, booths, house_locations, distance_constraint, paths)
        
        return render_template('index.html', booths=len(booths), image="static/city_map.png")
    
    return render_template('index.html', booths=None)

if __name__ == "__main__":
    app.run(debug=True)