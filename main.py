from Qt import QtWidgets

from NodeGraphQt import NodeGraph, PropertiesBinWidget

from Resource_Calculator import ProductionNode

# ---------------------------------------------------------------------------
# Graph wiring
# ---------------------------------------------------------------------------

def build_graph():
    app = QtWidgets.QApplication([])

    # ── create graph ──────────────────────────────────────────────────────
    graph = NodeGraph()
    graph.register_node(ProductionNode)

    # style tweaks
    graph.set_background_color(18, 18, 28)
    graph.set_grid_mode(1)   # dots

    # ── create properties bin ───────────────────────────────────────────────
    properties_bin = PropertiesBinWidget(parent=None, node_graph=graph)

    # ── toolbar ───────────────────────────────────────────────────────────
    viewer = graph.widget
    viewer.setWindowTitle("Factory Production Planner  -  NodeGraphQt")
    viewer.resize(1280, 760)

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

    lbl = QtWidgets.QLabel("  Factory Production Planner  |  ")
    toolbar.addWidget(lbl)


    btn_add = QtWidgets.QPushButton("+  Add Node")
    btn_delete_node = QtWidgets.QPushButton("🗑️  Delete Node")
    btn_recalc = QtWidgets.QPushButton("⟳  Recalculate All")
    btn_show_properties = QtWidgets.QPushButton("🗂️  Show Properties Bin")

    toolbar.addWidget(btn_add)
    toolbar.addWidget(btn_delete_node)
    toolbar.addSeparator()
    toolbar.addWidget(btn_recalc)
    toolbar.addSeparator()
    toolbar.addWidget(btn_show_properties)


    def add_node():
        node = graph.create_node(
            "factory.nodes.ProductionNode",
            name="Step",
            pos=[0, 0],
            push_undo=True,
        )
        node.recalculate()

    def delete_selected_nodes():
        for node in graph.selected_nodes():
            graph.delete_node(node)

    def recalculate_all():
        """Recalculate every node in the graph (topological ordering not
        strictly required here because each node recursively walks upstream,
        but we still visit all nodes to refresh standalone ones)."""
        visited = set()

        def visit(n):
            if id(n) in visited:
                return
            visited.add(id(n))
            if isinstance(n, ProductionNode):
                n.recalculate()

        for node in graph.all_nodes():
            visit(node)


    btn_add.clicked.connect(add_node)
    btn_recalc.clicked.connect(recalculate_all)
    btn_show_properties.clicked.connect(properties_bin.show)
    btn_delete_node.clicked.connect(delete_selected_nodes)

    # ── wrap viewer in a window with toolbar ──────────────────────────────
    main_widget = QtWidgets.QWidget()
    main_widget.setWindowTitle(viewer.windowTitle())
    main_widget.resize(1280, 760)
    layout = QtWidgets.QVBoxLayout(main_widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    layout.addWidget(toolbar)
    layout.addWidget(viewer)

    # ── auto-recalculate on connection changes ────────────────────────────
    def on_connection_changed(disconnected, connected):
        recalculate_all()

    graph.port_connected.connect(on_connection_changed)
    graph.port_disconnected.connect(on_connection_changed)

    def on_property_changed(node, prop_name):
        # react to any production property changing
        if (prop_name in ("input_qty", "num_outputs", "time", "machines")
                or prop_name.startswith("out_qty_")
                or prop_name.startswith("out_name_")):
            recalculate_all()

    graph.property_changed.connect(on_property_changed)


    # ── load example graph from JSON file ────────────────────────────────
    import json
    import os
    json_path = os.path.join(os.path.dirname(__file__), "example_graph.json")
    with open(json_path, "r") as f:
        data = json.load(f)

    node_objs = []
    # Create nodes
    for node_data in data.get("nodes", []):
        node = graph.create_node(
            node_data["type"],
            name=node_data.get("name", "Node"),
            pos=node_data.get("pos", [0, 0])
        )
        for prop, value in node_data.get("properties", {}).items():
            node.set_property(prop, value)
        node_objs.append(node)

    # Create connections
    for conn in data.get("connections", []):
        from_idx, from_port = conn["from"]
        to_idx, to_port = conn["to"]
        node_objs[from_idx].output(from_port).connect_to(node_objs[to_idx].input(to_port))

    recalculate_all()
    graph.fit_to_selection()

    main_widget.show()
    app.exec()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    build_graph()