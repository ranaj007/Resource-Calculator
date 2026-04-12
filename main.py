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
    viewer.setWindowTitle("Factory Production Planner  –  NodeGraphQt")
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

    # ── seed with an example chain ────────────────────────────────────────
    #
    #   Mine Ore  ──[ore]──►  Smelt Ingots  ──[ingots]──►  Forge Parts
    #             ╲─[slag]──►  Slag Dump
    #
    n1 = graph.create_node("factory.nodes.ProductionNode", name="Mine Ore",     pos=[-500,   0])
    n2 = graph.create_node("factory.nodes.ProductionNode", name="Smelt Ingots", pos=[ -100,  -80])
    n3 = graph.create_node("factory.nodes.ProductionNode", name="Forge Parts",  pos=[  300,  -80])
    n4 = graph.create_node("factory.nodes.ProductionNode", name="Slag Dump",    pos=[ -100,   350])

    # Mine Ore: no input, 2 outputs – ore and slag
    n1.set_property("input_qty",   "0")
    n1.set_property("num_outputs", "2")
    n1.set_property("out_qty_0",   "30")   # ore at 30 u/s
    n1.set_property("out_name_0",  "ore")
    n1.set_property("out_qty_1",   "5")    # slag at  5 u/s
    n1.set_property("out_name_1",  "slag")
    n1.set_property("time",        "1")

    # Smelt Ingots: consumes ore, produces ingots
    n2.set_property("input_qty",   "3")
    n2.set_property("num_outputs", "1")
    n2.set_property("out_qty_0",   "1")
    n2.set_property("time",        "2")

    # Forge Parts: consumes ingots, produces parts
    n3.set_property("input_qty",   "2")
    n3.set_property("num_outputs", "1")
    n3.set_property("out_qty_0",   "1")
    n3.set_property("time",        "5")

    # Slag Dump: consumes slag (no useful output)
    n4.set_property("input_qty",   "1")
    n4.set_property("num_outputs", "1")
    n4.set_property("out_qty_0",   "0")
    n4.set_property("time",        "1")

    # wire up
    n1.output(0).connect_to(n2.input(0))   # ore   → smelter
    n1.output(1).connect_to(n4.input(0))   # slag  → dump
    n2.output(0).connect_to(n3.input(0))   # ingots → forge

    recalculate_all()
    graph.fit_to_selection()

    n1.updating_ports = False
    n2.updating_ports = False
    n3.updating_ports = False
    n4.updating_ports = False

    main_widget.show()
    app.exec()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    build_graph()