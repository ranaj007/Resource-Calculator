"""
NodeGraphQt - Output Row Widget Node
A custom node widget that displays output row data in a compact, styled manner.
"""

from NodeGraphQt import BaseNode
from NodeGraphQt.widgets.node_widgets import NodeBaseWidget

from Qt import QtWidgets, QtGui, QtCore

from styles import COLORS, FONT_MONO, CHAR_WIDTH, QLineEdit_STYLE

QLabelGreen_STYLE = f"""
            color: {COLORS["type_fgg"]};
            background: {COLORS["gbadge_bg"]};
            font-family: {FONT_MONO};
            font-size: 10px;
            border-radius: 3px;
        """

QLabelRed_STYLE = f"""
            color: {COLORS["type_fgr"]};
            background: {COLORS["rbadge_bg"]};
            font-family: {FONT_MONO};
            font-size: 10px;
            border-radius: 3px;
        """

# ────────────────────────────────────────────────────────────────────────────
#  Compact input row widget  (input_qty │ Time (s) │ Machines)
# ────────────────────────────────────────────────────────────────────────────


class InputRowWidget(NodeBaseWidget):
    """
    Compact input row widget embeddable in a NodeGraphQt node.

    Usage inside a custom node::

        widget = InputRowWidget(parent=self.view)
        widget.onNameChange(update_ports)  # optional callback for name changes
        widget.onOutputChange(update_calculations)  # optional callback for output changes
        self.add_custom_widget(widget, tab="Data")
    """

    def __init__(self, parent=None, name="input_name", label="", input_qty=1):
        if label == "":
            label = "Input qty          Time (s)           Machines"
        super().__init__(parent=parent, name=name, label=label)

        # ── Outer container ──────────────────────────────────────────────
        container = QtWidgets.QWidget()
        container.setStyleSheet(f"""
            QWidget {{
                background: {COLORS["bg"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 4px;
            }}
        """)

        container.setMaximumWidth(CHAR_WIDTH * 29)  # set max width to prevent excessive stretching

        row = QtWidgets.QHBoxLayout(container)
        row.setContentsMargins(2, 2, 2, 2)
        row.setSpacing(1)

        # Input quantity
        self.input_qty = QtWidgets.QLineEdit()
        self.input_qty.setValidator(QtGui.QDoubleValidator(0.0, 1e9, 5))  # allow only positive floats with 5 decimal places
        self.input_qty.setStyleSheet(QLineEdit_STYLE)
        #self.input_qty.setFixedWidth(CHAR_WIDTH * 6)
        self.input_qty.setText(str(input_qty))

        # Time (s)
        self.time = QtWidgets.QLineEdit()
        self.time.setValidator(QtGui.QDoubleValidator(0.0, 1e9, 5))  # allow only positive floats with 5 decimal places
        self.time.setStyleSheet(QLineEdit_STYLE)
        #self.time.setFixedWidth(CHAR_WIDTH * 6)
        self.time.setText("1")

        # Machines
        # set text to right-align
        self.machines = QtWidgets.QLabel("5 (5.00)")
        self.machines.setStyleSheet(f"""
            color: {COLORS["val_fg"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 3px;
            font-family: {FONT_MONO};
            font-size: 10px;
        """)
        #self.machines.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        #self.machines.setFixedWidth(CHAR_WIDTH * 10)

        row.addWidget(self.input_qty)
        row.addWidget(self.time)
        row.addWidget(self.machines)

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
    def get_input_qty(self) -> float | None:
        """Get the current input quantity."""
        return self.convert_float(self.input_qty.text())

    def get_time(self) -> float | None:
        """Get the current time (s)."""
        return self.convert_float(self.time.text())

    def get_machines(self) -> float | None:
        """Get the current machine count."""
        return self.convert_float(self.machines.text())

    def set_input_qty(self, qty: float | None) -> None:
        """Set the input quantity."""
        self.input_qty.setText(self.convert_str(qty))

    def set_time(self, value: float | None) -> None:
        """Set the time (s) value."""
        self.time.setText(self.convert_str(value))

    def set_machines(self, value: float | None) -> None:
        """Set the machine count value."""
        self.machines.setText(value)

    def onInputChange(self, callback):
        """Connect a callback function to the input quantity text change event."""
        self.input_qty.textChanged.connect(callback)

    def onTimeChange(self, callback):
        """Connect a callback function to the time text change event."""
        self.time.textChanged.connect(callback)

    # ── Required NodeBaseWidget overrides ─────────────────────────────────
    def get_value(self):
        return

    def set_value(self, value):
        return


# ────────────────────────────────────────────────────────────────────────────
#  Example node using the widget
# ────────────────────────────────────────────────────────────────────────────
class InputRowNode(BaseNode):
    """
    A node that embeds an InputRowWidget.
    """

    __identifier__ = "io.example"
    NODE_NAME = "Input Row Viewer"

    def __init__(self):
        super().__init__()

        # Ports
        self.add_input("in")
        self.add_output("out")

        # Embed the widget
        self.input_row_widget = InputRowWidget(
            parent=self.view,
            name="input_name",
            label="",
        )
        self.add_custom_widget(self.input_row_widget, tab="widget")

        self.input_row_widget.set_input_qty(3342.05)
        self.input_row_widget.set_time(1742.34)


# ────────────────────────────────────────────────────────────────────────────
#  Standalone demo
# ────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    from NodeGraphQt import NodeGraph

    app = QtWidgets.QApplication(sys.argv)

    graph = NodeGraph()
    graph.register_node(InputRowNode)

    viewer = graph.widget
    viewer.resize(900, 600)
    viewer.show()

    node = graph.create_node("io.example.InputRowNode", name="My Input Row Node")
    node.set_pos(0, 0)

    sys.exit(app.exec())
