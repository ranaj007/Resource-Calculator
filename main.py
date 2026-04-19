import os

from ProductionGraph import ProductionGraph

def main():
    graph = ProductionGraph()

    # Initial load
    default_json_path = os.path.join(os.path.dirname(__file__), "example_graph.json")
    graph.load_graph_from_json(default_json_path)

    graph.start()

if __name__ == "__main__":
    main()