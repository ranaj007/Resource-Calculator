"""
NodeGraphQt - Dictionary Widget Node
A custom node widget that displays dictionary data in a compact, styled manner.
"""

from NodeGraphQt import BaseNode
from NodeGraphQt.widgets.node_widgets import NodeBaseWidget

from Qt import QtWidgets, QtCore, QtGui


# ── Colour palette (dark-terminal aesthetic) ────────────────────────────────
COLORS = {
    "bg":        "#1a1d23",
    "row_alt":   "#1f2330",
    "border":    "#2e3347",
    "key_fg":    "#7eb8da",   # cool blue  – key column
    "val_fg":    "#c8d6e5",   # near-white – value column
    "type_fg":   "#6a9e6a",   # muted green – type badge
    "header_bg": "#151820",
    "header_fg": "#4a90b8",
    "badge_bg":  "#1c2b1c",
    "sel_bg":    "#25304a",
    "scroll":    "#2e3347",
}

FONT_MONO = "Consolas, 'Courier New', monospace"


# ────────────────────────────────────────────────────────────────────────────
#  Compact row widget  (key │ value │ type-badge)
# ────────────────────────────────────────────────────────────────────────────
class _DetailsRow(QtWidgets.QWidget):
    """Single key/value row."""

    def __init__(self, key, value, alt=False, parent=None):
        super().__init__(parent)
        self._alt = alt
        self._build(key, value)

    def _type_badge(self, value):
        t = type(value).__name__
        abbreviations = {
            "str": "str", "int": "int", "float": "flt",
            "bool": "bool", "list": "lst", "dict": "dct",
            "NoneType": "nil", "tuple": "tup",
        }
        return abbreviations.get(t, t[:3])

    def _format_value(self, value):
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is None:
            return "null"
        if isinstance(value, (list, tuple)):
            inner = ", ".join(str(v) for v in value[:4])
            if len(value) > 4:
                inner += f" +{len(value)-4}"
            return f"[{inner}]"
        if isinstance(value, dict):
            return f"{{…{len(value)} keys}}"
        return str(value)

    def _build(self, key, value):
        bg = COLORS["row_alt"] if self._alt else COLORS["bg"]

        self.setStyleSheet(f"""
            QWidget {{ background: {bg}; }}
        """)

        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(6, 2, 6, 2)
        row.setSpacing(6)

        # Key label
        key_lbl = QtWidgets.QLabel(str(key))
        key_lbl.setStyleSheet(f"""
            color: {COLORS['key_fg']};
            font-family: {FONT_MONO};
            font-size: 11px;
            font-weight: bold;
        """)
        key_lbl.setToolTip(str(key))

        # Separator
        sep = QtWidgets.QLabel("│")
        sep.setStyleSheet(f"color: {COLORS['border']}; font-size: 11px;")
        sep.setFixedWidth(8)

        # Value label
        val_lbl = QtWidgets.QLabel(self._format_value(value))
        val_lbl.setFixedWidth(30)
        val_lbl.setStyleSheet(f"""
            color: {COLORS['val_fg']};
            font-family: {FONT_MONO};
            font-size: 11px;
        """)
        val_lbl.setToolTip(repr(value))

        row.addWidget(key_lbl)
        row.addWidget(sep)
        row.addWidget(val_lbl, 1)

# ────────────────────────────────────────────────────────────────────────────
#  The NodeBaseWidget wrapper
# ────────────────────────────────────────────────────────────────────────────
class DetailsDisplayWidget(NodeBaseWidget):
    """
    Compact dictionary viewer embeddable in a NodeGraphQt node.

    Usage inside a custom node::

        widget = DetailsDisplayWidget(parent=self.view)
        widget.set_dict({"alpha": 1, "beta": "hello", "gamma": [1, 2, 3]})
        self.add_custom_widget(widget, tab="Data")
    """

    def __init__(self, parent=None, name="dict_display", label=""):
        super().__init__(parent=parent, name=name, label=label)

        self._data: dict = {}

        # ── Outer container ──────────────────────────────────────────────
        self.container = QtWidgets.QWidget()
        self.container.setStyleSheet(f"""
            QWidget {{
                background: {COLORS['bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
            }}
        """)

        self._outer = QtWidgets.QVBoxLayout(self.container)
        self._outer.setContentsMargins(0, 0, 0, 0)
        self._outer.setSpacing(0)

        # ── Scroll area for rows ──────────────────────────────────────────
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: {COLORS['scroll']};
                width: 10px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['bg']};
                border-radius: 3px;
                min-height: 10px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

        self._rows_widget = QtWidgets.QWidget()
        self._rows_widget.setStyleSheet(f"background: {COLORS['bg']}; border: none;")
        self._rows_layout = QtWidgets.QVBoxLayout(self._rows_widget)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(0)
        self._rows_layout.addStretch()

        self.scroll.setWidget(self._rows_widget)
        self._outer.addWidget(self.scroll)

        # ── Finalize ───────────────────────────────────────────────────────
        self.set_custom_widget(self.container)

    
    def _set_height(self):
        # Adjust container and scroll heights based on number of rows
        row_count = len(self._data)
        height = min(20 * row_count, 200)  # 20px per row, max 200px
        self.container.setFixedHeight(height)  # max height with scrollbar
        self.scroll.setFixedHeight(height)  # per-row height


    # ── Public API ────────────────────────────────────────────────────────
    def set_dict(self, data: dict):
        """Replace the displayed dictionary."""
        assert isinstance(data, dict), "data must be a dict"
        self._data = data
        self._rebuild_rows()
        #self.update()

    def get_dict(self) -> dict:
        """Return the currently displayed dictionary."""
        return dict(self._data)

    def update_key(self, key, value):
        """Add or update a single key without rebuilding all rows."""
        self._data[key] = value
        self._rebuild_rows()
        #self.update()

    def remove_key(self, key):
        """Remove a key if present."""
        self._data.pop(key, None)
        self._rebuild_rows()
        #self.update()

    # ── Required NodeBaseWidget overrides ─────────────────────────────────
    def get_value(self):
        return self._data

    def set_value(self, value):
        #if isinstance(value, dict):
            #self.set_dict(value)
            pass

    # ── Internal ──────────────────────────────────────────────────────────
    def _rebuild_rows(self):
        # Clear existing rows (keep the trailing stretch)
        while self._rows_layout.count() > 1:
            item = self._rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, (k, v) in enumerate(self._data.items()):
            row = _DetailsRow(k, v, alt=(i % 2 == 1))
            self._rows_layout.insertWidget(i, row)

        self._set_height()


# ────────────────────────────────────────────────────────────────────────────
#  Example node using the widget
# ────────────────────────────────────────────────────────────────────────────
class DetailsNode(BaseNode):
    """
    A node that embeds a DetailsDisplayWidget.
    Drop this into your graph and call node.set_dict({...}) to populate it.
    """

    __identifier__ = "io.example"
    NODE_NAME = "Details Viewer"

    def __init__(self):
        super().__init__()

        # Ports
        self.add_input("in")
        self.add_output("out")

        # Embed the widget
        self._details_widget = DetailsDisplayWidget(
            parent=self.view,
            name="details_display",
            label="",
        )
        self.add_custom_widget(self._details_widget, tab="widget")

        # Seed with example data
        self.set_dict({
            "vines (ideal)": 2.212,
            "vines (real)":    0.751,
            "plant balls (ideal)":  406.7,
            "plant balls (real)":  386.7,
        })

    def set_dict(self, data: dict):
        """Populate the embedded dictionary widget."""
        self._details_widget.set_dict(data)

    def get_dict(self) -> dict:
        return self._details_widget.get_dict()


# ────────────────────────────────────────────────────────────────────────────
#  Standalone demo
# ────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    from NodeGraphQt import NodeGraph

    app = QtWidgets.QApplication(sys.argv)

    graph = NodeGraph()
    graph.register_node(DetailsNode)

    viewer = graph.widget
    viewer.resize(900, 600)
    viewer.show()

    node = graph.create_node("io.example.DetailsNode", name="My Details Node")
    node.set_pos(0, 0)

    sys.exit(app.exec())