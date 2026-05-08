from NodeGraphQt.widgets.node_widgets import NodeBaseWidget

from Qt import QtWidgets

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

class TextInputNodeWidget(NodeBaseWidget):
    """A basic custom node widget for text input."""
    def __init__(self, parent=None, name="text_display", label=""):
        super().__init__(parent=parent, name=name, label=label)



        label1 = QtWidgets.QLabel("top")
        label2 = QtWidgets.QLabel("bottom")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label1)
        layout.addWidget(label2)

        container = QtWidgets.QWidget()
        container.setLayout(layout)

        # ── Finalize ───────────────────────────────────────────────────────
        self.set_custom_widget(container)


    def get_value(self):
        return None


    def set_value(self, value):
        return

class TextInputNodeWidget2(NodeBaseWidget):
    """A basic custom node widget for text input."""
    def __init__(self, parent=None, name="text_display", label=""):
        super().__init__(parent=parent, name=name, label=label)


        container = QtWidgets.QWidget()
        container.setStyleSheet(f"""
            QWidget {{
                background: {COLORS['bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
            }}
        """)

        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._list_widget = QtWidgets.QListWidget()
        self._list_widget.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                color: {COLORS['val_fg']};
                font-family: {FONT_MONO};
                font-size: 11px;
            }}
            QListWidget::item {{
                padding: 4px 6px;
            }}
            QListWidget::item:nth-child(odd) {{
                background: {COLORS['row_alt']};
            }}
            QListWidget::item:selected {{
                background: {COLORS['sel_bg']};
            }}
        """)

        label1 = QtWidgets.QLabel("top")
        label2 = QtWidgets.QLabel("bottom")

        label_style = f"""
            QLabel {{
                color: {COLORS['val_fg']};
                font-family: {FONT_MONO};
                font-size: 11px;
            }}
        """
        label1.setStyleSheet(label_style)
        label2.setStyleSheet(label_style)

        layout.addWidget(label1)
        layout.addWidget(self._list_widget)
        layout.addWidget(label2)

        list_items = ["Item 1", "Item 2"]
        self._list_widget.addItems(list_items)

        # ── Finalize ───────────────────────────────────────────────────────
        self.set_custom_widget(container)


    def get_value(self):
        return None


    def set_value(self, value):
        return