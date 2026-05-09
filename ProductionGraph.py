import json
from Qt import QtWidgets
from ProductionNode import ProductionNode
from NodeGraphQt import NodeGraph, PropertiesBinWidget

# ---------------------------------------------------------------------------
# ProductionGraph class definition
# ---------------------------------------------------------------------------

class ProductionGraph():
    def __init__(self, window_size=(1280, 760)):
        self.app = QtWidgets.QApplication([])

        # ── create graph ──────────────────────────────────────────────────────
        self.graph = NodeGraph()
        self.graph.register_node(ProductionNode)

        # ── style tweaks ───────────────────────────────────────────────────────
        self.graph.set_background_color(18, 18, 28)
        self.graph.set_grid_mode(1) # dots

        # ── create properties bin ───────────────────────────────────────────────
        self.properties_bin = PropertiesBinWidget(parent=None, node_graph=self.graph)

        # ── toolbar ───────────────────────────────────────────────────────────
        viewer = self.graph.widget
        viewer.setWindowTitle("Factory Production Planner  -  NodeGraphQt")
        viewer.resize(*window_size)

        toolbar = QtWidgets.QToolBar("Toolbar")
        toolbar.setMovable(False)

        _style_sheet = """
            QToolBar { background: #12121e; border-bottom: 1px solid #2a2a3e; spacing: 8px; padding: 4px 8px; }
            QPushButton {
                background: #252540; color: #c8c8ff; border: 1px solid #4040a0;
                border-radius: 4px; padding: 6px 16px; font-size: 13px;
            }
            QPushButton:hover  { background: #303060; border-color: #8080ff; }
            QPushButton:pressed{ background: #1a1a30; }
            QLabel { color: #7070c0; font-size: 12px; }
        """
        toolbar.setStyleSheet(_style_sheet)

        lbl = QtWidgets.QLabel("  Factory Planner  |  ")
        toolbar.addWidget(lbl)

        btn_output_add = QtWidgets.QPushButton("+ Output")
        btn_output_remove = QtWidgets.QPushButton("- Output")
        btn_add_node = QtWidgets.QPushButton("+  Add Node")
        btn_delete_node = QtWidgets.QPushButton("🗑️  Delete Node")
        btn_recalc = QtWidgets.QPushButton("⟳  Recalculate All")
        btn_show_props = QtWidgets.QPushButton("🗂️  Show Properties Bin")
        btn_load = QtWidgets.QPushButton("📂  Load Graph")
        btn_save = QtWidgets.QPushButton("💾  Save Graph")

        toolbar.addWidget(btn_output_add)
        toolbar.addWidget(btn_output_remove)
        toolbar.addSeparator()
        toolbar.addWidget(btn_add_node)
        toolbar.addWidget(btn_delete_node)
        toolbar.addSeparator()
        toolbar.addWidget(btn_recalc)
        toolbar.addSeparator()
        toolbar.addWidget(btn_show_props)
        toolbar.addSeparator()
        toolbar.addWidget(btn_load)
        toolbar.addWidget(btn_save)

        btn_output_add.clicked.connect(self.add_output_to_selected_nodes)
        btn_output_remove.clicked.connect(self.remove_output_from_selected_nodes)
        btn_add_node.clicked.connect(self.add_node)
        btn_recalc.clicked.connect(self.recalculate_all)
        btn_show_props.clicked.connect(self.properties_bin.show)
        btn_delete_node.clicked.connect(self.delete_selected_nodes)
        btn_load.clicked.connect(self.on_load_clicked)
        btn_save.clicked.connect(self.on_save_clicked)

        # ── wrap viewer in a window with toolbar ──────────────────────────────
        self.main_widget = QtWidgets.QWidget()
        self.main_widget.setWindowTitle(viewer.windowTitle())
        self.main_widget.resize(*window_size)

        layout = QtWidgets.QVBoxLayout(self.main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(toolbar)
        layout.addWidget(viewer)

        self.loading = False  # flag to prevent unwanted recalculations during JSON loading

        # ── auto-recalculate on connection changes ────────────────────────────
        def on_connection_changed(disconnected, connected):
            self._recalculate_node_and_downstream(connected.node())

        self.graph.port_connected.connect(on_connection_changed)
        self.graph.port_disconnected.connect(on_connection_changed)

        # ── auto-recalculate on property changes ───────────────────────────────
        def on_property_changed(node, prop_name):
            if (prop_name in ("input_qty", "num_outputs", "time", "machines")
                or prop_name.startswith("out_qty_")
                or prop_name.startswith("out_name_")):
                self._recalculate_node_and_downstream(node)

        self.graph.property_changed.connect(on_property_changed)
    

    def start(self):
        """Show the main window and start the Qt event loop."""
        self.main_widget.show()
        self.app.exec()


    def add_node(self) -> None:
        """Add a new production node to the graph."""
        node = self.graph.create_node(
            "factory.nodes.ProductionNode",
            name="Step",
            pos=[0, 0],
            push_undo=True,
        )
        node: ProductionNode
        node.recalculate()


    def delete_selected_nodes(self) -> None:
        """Delete all selected nodes from the graph."""
        for node in self.graph.selected_nodes():
            self.graph.delete_node(node)


    def add_output_to_selected_nodes(self) -> None:
        """Add an output port to all selected nodes."""
        for node in self.graph.selected_nodes():
            if isinstance(node, ProductionNode):
                node: ProductionNode
                node.add_port()
        node.recalculate()


    def remove_output_from_selected_nodes(self) -> None:
        """Remove the last output port from all selected nodes."""
        for node in self.graph.selected_nodes():
            if isinstance(node, ProductionNode):
                node: ProductionNode
                node.remove_port()
        node.recalculate()


    def recalculate_all(self) -> None:
        """Recalculate every node in the graph (topological ordering not
        strictly required here because each node recursively walks upstream,
        but we still visit all nodes to refresh standalone ones)."""
        if self.loading:
            return  # prevent recalculations while loading from JSON
        
        all_nodes = self.graph.all_nodes()

        connections = {}

        for node in all_nodes:
            node: ProductionNode
            input_port = node.get_input(0)
            connected_ports = input_port.connected_ports()
            
            connections[node] = [p.node() for p in connected_ports]
               
        visited = set()

        def visit(n):
            if id(n) in visited:
                return
            visited.add(id(n))
            if isinstance(n, ProductionNode):
                n.recalculate()

        while connections:
            to_visit = [n for n, deps in connections.items() if all(id(d) in visited for d in deps)]
            if not to_visit:
                # Circular dependency detected, break the loop to avoid infinite recursion
                break
            for n in to_visit:
                visit(n)
                visited.add(id(n))
                del connections[n]

    
    def _recalculate_node_and_downstream(self, node: ProductionNode, visited=None) -> None:
        """Recursively recalculate the given node and all downstream nodes."""
        if visited is None:
            visited = set()
        if id(node) in visited:
            return
        visited.add(id(node))
        node.recalculate()
        for output_port in node.output_ports():
            for conn in output_port.connected_ports():
                downstream_node = conn.node()
                if isinstance(downstream_node, ProductionNode):
                    self._recalculate_node_and_downstream(downstream_node, visited)


    def clear_graph(self) -> None:
        """Delete all nodes from the graph."""
        for node in self.graph.all_nodes():
            self.graph.delete_node(node)


    def load_graph_from_json(self, json_path: str) -> None:
        """Load a graph from a JSON file, replacing the current graph contents."""
        self.loading = True
        self.clear_graph()
        with open(json_path, "r") as f:
            data = json.load(f)
            data: dict
        node_objs = []

        for node_data in data.get("nodes", []):
            node_data: dict
            node = self.graph.create_node(
                node_data["type"],
                name=node_data.get("name", "Node"),
                pos=node_data.get("pos", [0, 0])
            )

            if node_data["type"] == "factory.nodes.ProductionNode":
                node: ProductionNode
                node.loading = True  # set loading flag to prevent recalculations during setup
            
            # get num_outputs from node_data["properties"] if it exists, otherwise default to 1
            num_outputs = int(node_data.get("properties", {}).get("num_outputs", 1)) - 1
            for i in range(num_outputs):
                    node.add_port()
            
            for i, output_data in enumerate(node_data.get("outputs", [])):
                name = output_data.get("name", f"output_{i}")
                qty = output_data.get("qty", "1")
                output_widget = node.get_output_widget(i)
                if output_widget:
                    output_widget.set_output_name(name)
                    output_widget.set_output_qty(qty)

            for prop, value in node_data.get("properties", {}).items():
                try:
                    node.set_property(prop, value)
                except Exception as e:
                    print(f"Warning: Failed to set property '{prop}' on node '{node.name()}': {e}")
            
            node_objs.append(node)

        for conn in data.get("connections", []):
            from_idx, from_port = conn["from"]
            to_idx, to_port = conn["to"]
            node_objs[from_idx].get_output(from_port).connect_to(node_objs[to_idx].get_input(to_port))
        self.loading = False
        for node in node_objs:
            if isinstance(node, ProductionNode):
                node: ProductionNode
                node.loading = False  # unset loading flag after setup is complete
        self.recalculate_all()
        self.graph.fit_to_selection()


    def save_graph_to_json(self, json_path: str) -> None:
        """Save the current graph to a JSON file."""
        nodes = []
        node_index = {}
        for idx, node in enumerate(self.graph.all_nodes()):
            node_index[node] = idx
            node_data = {
                "type": type(node).type_,
                "name": node.name(),
                "pos": node.pos(),
                "properties": {k: v for k, v in node.model._custom_prop.items()},
                "outputs": [
                    {
                        "name": node.get_output_widget(i).get_output_name(),
                        "qty": node.get_output_widget(i).get_output_qty()
                    }
                    for i in range(len(node.output_ports()))
                ]
            }
            nodes.append(node_data)
        connections = []
        for node in self.graph.all_nodes():
            if isinstance(node, ProductionNode):
                node: ProductionNode
                
            idx_from = node_index[node]
            for i, port in enumerate(node.output_ports()):
                for conn in port.connected_ports():
                    node_to = conn.node()
                    idx_to = node_index[node_to]
                    in_port_idx = node_to.input_ports().index(conn)
                    connections.append({"from": [idx_from, i], "to": [idx_to, in_port_idx]})
        data = {"nodes": nodes, "connections": connections}
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)


    def on_load_clicked(self) -> None:
        """Open a file dialog to select a JSON file, then load the graph from that file."""
        options = QtWidgets.QFileDialog.Options()
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.main_widget, "Load Graph from JSON", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_path:
            self.load_graph_from_json(file_path)


    def on_save_clicked(self) -> None:
        """Open a file dialog to select a JSON file path, then save the graph to that file."""
        options = QtWidgets.QFileDialog.Options()
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.main_widget, "Save Graph to JSON", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_path:
            self.save_graph_to_json(file_path)
