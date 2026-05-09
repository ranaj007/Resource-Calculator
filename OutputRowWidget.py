"""
NodeGraphQt - Output Row Widget Node
A custom node widget that displays output row data in a compact, styled manner.
"""

from NodeGraphQt import BaseNode
from NodeGraphQt.widgets.node_widgets import NodeBaseWidget

from Qt import QtWidgets, QtGui

from styles import COLORS, FONT_MONO, CHAR_WIDTH, QLineEdit_STYLE

QLabelGreen_STYLE = f"""
            color: {COLORS['type_fgg']};
            background: {COLORS['gbadge_bg']};
            font-family: {FONT_MONO};
            font-size: 10px;
            border-radius: 3px;
        """

QLabelRed_STYLE = f"""
            color: {COLORS['type_fgr']};
            background: {COLORS['rbadge_bg']};
            font-family: {FONT_MONO};
            font-size: 10px;
            border-radius: 3px;
        """

# ────────────────────────────────────────────────────────────────────────────
#  Compact row widget  (output_name │ output_qty │ output_ideal │ output_real)
# ────────────────────────────────────────────────────────────────────────────

class OutputRowWidget(NodeBaseWidget):
    """
    Compact output row widget embeddable in a NodeGraphQt node.

    Usage inside a custom node::

        widget = OutputRowWidget(parent=self.view)
        widget.onNameChange(update_ports)  # optional callback for name changes
        widget.onOutputChange(update_calculations)  # optional callback for output changes
        self.add_custom_widget(widget, tab="Data")
    """

    def __init__(self, parent=None, name="output_name", label="", output_qty=1):
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
        self.output_name.setText(str(name))
        #padding: 2px 4px;

        # Output quantity
        self.output_qty = QtWidgets.QLineEdit()
        self.output_qty.setValidator(QtGui.QDoubleValidator(0.0, 1e9, 5))  # allow only positive floats with 5 decimal places
        self.output_qty.setStyleSheet(QLineEdit_STYLE)
        self.output_qty.setFixedWidth(CHAR_WIDTH * 6)
        self.output_qty.setText(str(output_qty))

        # Output ideal
        self.output_ideal = QtWidgets.QLabel(str(output_qty))
        self.output_ideal.setStyleSheet(QLabelGreen_STYLE)
        self.output_ideal.setFixedWidth(CHAR_WIDTH * 6)

        # Output real
        self.output_real = QtWidgets.QLabel(str(output_qty))
        self.output_real.setStyleSheet(QLabelGreen_STYLE)
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
    
    def convert_str(self, value):
        if not isinstance(value, str):
            value = f"{value:g}"
        return value

    # ── Public API ────────────────────────────────────────────────────────
    def get_output_name(self) -> str:
        """Get the current output name."""
        return self.output_name.text()
    
    def get_output_qty(self) -> float | None:
        """Get the current output quantity."""
        return self.convert_float(self.output_qty.text())
    
    def get_output_ideal(self) -> float | None:
        """Get the current ideal output."""
        return self.convert_float(self.output_ideal.text())
    
    def get_output_real(self) -> float | None:
        """Get the current real output."""
        return self.convert_float(self.output_real.text())
    
    def set_output_name(self, name: str) -> None:
        """Set the output name."""
        self.output_name.setText(str(name))

    def set_output_qty(self, qty: float | None) -> None:
        """Set the output quantity."""
        self.output_qty.setText(self.convert_str(qty))
    
    def set_output_ideal(self, value: float | None) -> None:
        """Set the ideal output value."""
        self.output_ideal.setText(self.convert_str(value))

    def set_output_real(self, value: float | None) -> None:
        """Set the real output value."""
        self.output_real.setText(self.convert_str(value))

        if float(value) < self.get_output_ideal():
            self.output_real.setStyleSheet(QLabelRed_STYLE)
        else:
            self.output_real.setStyleSheet(QLabelGreen_STYLE)

    def onNameChange(self, callback):
        """Connect a callback function to the output name text change event."""
        self.output_name.textChanged.connect(callback)

    def onOutputChange(self, callback):
        """Connect a callback function to the output quantity text change event."""
        self.output_qty.textChanged.connect(callback)

    
    # ── Required NodeBaseWidget overrides ─────────────────────────────────
    def get_value(self):
        return

    def set_value(self, value):
        return

# ────────────────────────────────────────────────────────────────────────────
#  Example node using the widget
# ────────────────────────────────────────────────────────────────────────────
class OutputRowNode(BaseNode):
    """
    A node that embeds an OutputRowWidget.
    """

    __identifier__ = "io.example"
    NODE_NAME = "Output Row Viewer"

    def __init__(self):
        super().__init__()

        # Ports
        self.add_input("in")
        self.add_output("out")

        # Embed the widget
        self.output_row_widget = OutputRowWidget(
            parent=self.view,
            name="output_name",
            label="",
        )
        self.add_custom_widget(self.output_row_widget, tab="widget")

        self.output_row_widget.set_output_ideal(3342.05)
        self.output_row_widget.set_output_real(1742.34)

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