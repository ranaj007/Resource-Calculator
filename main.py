import os
from ProductionGraph import ProductionGraph

def main():
    # clear counter.txt on startup
    counter_file_path = os.path.join(os.path.dirname(__file__), "counter.txt")
    with open(counter_file_path, "w") as f:
        f.write("0")
        
    graph = ProductionGraph()

    # Initial load
    default_json_path = os.path.join(os.path.dirname(__file__), "example_graph.json")
    graph.load_graph_from_json(default_json_path)

    # Start the graph editor
    graph.start()

if __name__ == "__main__":
    main()