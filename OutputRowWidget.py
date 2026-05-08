"""
NodeGraphQt - Output Row Widget Node
A custom node widget that displays output row data in a compact, styled manner.
"""

from NodeGraphQt import BaseNode
from NodeGraphQt.widgets.node_widgets import NodeBaseWidget

from Qt import QtWidgets

from styles import COLORS, FONT_MONO, CHAR_WIDTH, QLineEdit_STYLE

# ────────────────────────────────────────────────────────────────────────────
#  Compact row widget  (output_name │ output_qty │ output_ideal │ output_real)
# ────────────────────────────────────────────────────────────────────────────

class OutputRowWidget(NodeBaseWidget):
    """
    Compact dictionary viewer embeddable in a NodeGraphQt node.

    Usage inside a custom node::

        widget = OutputRowWidget(parent=self.view)
        self.add_custom_widget(widget, tab="Data")
    """

    def __init__(self, parent=None, name="dict_display", label=""):
        super().__init__(parent=parent, name=name, label=label)

        # ── Outer container ──────────────────────────────────────────────
        container = QtWidgets.QWidget()
        container.setStyleSheet(f"""
            QWidget {{
                background: {COLORS['bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
            }}
        """)

        row = QtWidgets.QHBoxLayout(container)
        row.setContentsMargins(2, 2, 2, 2)
        row.setSpacing(1)

        # Output name
        self.output_name = QtWidgets.QLineEdit()
        self.output_name.setStyleSheet(QLineEdit_STYLE)
        self.output_name.setFixedWidth(CHAR_WIDTH * 10)
        self.output_name.setText("output_name")
        #padding: 2px 4px;

        # Output quantity
        self.output_qty = QtWidgets.QLineEdit()
        self.output_qty.setStyleSheet(QLineEdit_STYLE)
        self.output_qty.setFixedWidth(CHAR_WIDTH * 6)
        self.output_qty.setText("3342.05")

        # Output ideal
        self.output_ideal = QtWidgets.QLabel("3342.05")
        self.output_ideal.setStyleSheet(f"""
            color: {COLORS['type_fgg']};
            background: {COLORS['gbadge_bg']};
            font-family: {FONT_MONO};
            font-size: 10px;
            border-radius: 3px;
        """)
        self.output_ideal.setFixedWidth(CHAR_WIDTH * 6)

        # Output real
        self.output_real = QtWidgets.QLabel("1742.34")
        self.output_real.setStyleSheet(f"""
            color: {COLORS['type_fgr']};
            background: {COLORS['rbadge_bg']};
            font-family: {FONT_MONO};
            font-size: 10px;
            border-radius: 3px;
        """)
        self.output_real.setFixedWidth(CHAR_WIDTH * 6)

        row.addWidget(self.output_name)
        row.addWidget(self.output_qty)
        row.addWidget(self.output_ideal)
        row.addWidget(self.output_real)

        # ── Finalize ───────────────────────────────────────────────────────
        self.set_custom_widget(container)


    # ── Helper Methods ────────────────────────────────────────────────────
    def convert_float(self, text):
        """Convert text to float, returning None if conversion fails."""
        try:
            return float(text)
        except ValueError:
            return None
        

    # ── Public API ────────────────────────────────────────────────────────
    def get_output_name(self):
        """Get the current output name."""
        return self.output_name.text()
    
    def get_output_qty(self):
        """Get the current output quantity."""
        return self.convert_float(self.output_qty.text())
    
    def get_output_ideal(self):
        """Get the current ideal output."""
        return self.convert_float(self.output_ideal.text())
    
    def get_output_real(self):
        """Get the current real output."""
        return self.convert_float(self.output_real.text())
    
    def calculate_outputs(self, machines=1, efficiency=1.0):
        """Calculate ideal and real outputs based on quantity, machine count, and efficiency."""
        try:
            qty = float(self.get_output_qty())
            ideal = qty / machines
            real = ideal * efficiency
            self.output_ideal.setText(f"{ideal:.2f}")
            self.output_real.setText(f"{real:.2f}")
        except ValueError:
            self.output_ideal.setText("error")
            self.output_real.setText("error")

    # ── Required NodeBaseWidget overrides ─────────────────────────────────
    def get_value(self):
        return self.get_output_qty()

    def set_value(self, value):
        return

# ────────────────────────────────────────────────────────────────────────────
#  Example node using the widget
# ────────────────────────────────────────────────────────────────────────────
class OutputRowNode(BaseNode):
    """
    A node that embeds an OutputRowWidget.
    Drop this into your graph and call node.set_dict({...}) to populate it.
    """

    __identifier__ = "io.example"
    NODE_NAME = "Output Row Viewer"

    def __init__(self):
        super().__init__()

        # Ports
        self.add_input("in")
        self.add_output("out")

        # Embed the widget
        self._output_row_widget = OutputRowWidget(
            parent=self.view,
            name="output_editor",
            label="",
        )
        self.add_custom_widget(self._output_row_widget, tab="widget")

# ────────────────────────────────────────────────────────────────────────────
#  Standalone demo
# ────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    from NodeGraphQt import NodeGraph

    app = QtWidgets.QApplication(sys.argv)

    graph = NodeGraph()
    graph.register_node(OutputRowNode)

    viewer = graph.widget
    viewer.resize(900, 600)
    viewer.show()

    node = graph.create_node("io.example.OutputRowNode", name="My Output Row Node")
    node.set_pos(0, 0)

    sys.exit(app.exec())