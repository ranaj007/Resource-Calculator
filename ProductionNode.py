"""
Factory Production Node Graph
==============================
Uses NodeGraphQt to build a production-chain planner.

Each node represents a production step with:
  - input_qty    : units consumed per cycle
  - num_outputs  : how many output ports to create
  - out_qty_N    : units produced per cycle on output port N
  - out_name_N   : display label for output port N
  - time         : seconds per cycle

The node calculates:
  machines_needed = ceil( upstream_rate / (input_qty / time) )
  port_rate[N]    = machines_needed * out_qty_N / time   (units / sec)
"""

from OutputRowWidget import OutputRowWidget
from InputRowWidget import InputRowWidget
from NodeGraphQt import BaseNode, Port
import math

# ---------------------------------------------------------------------------
# Custom Node
# ---------------------------------------------------------------------------

class ProductionNode(BaseNode):
    """
    A node representing one step in a production chain.

    Ports
    -----
    • input       - receives upstream output rate (units / sec), multi-input
    • output_N    - emits this node's output rate for product N (units / sec)

    Embedded properties (rendered as line-edit widgets inside the node)
    -------------------------------------------------------------------
    • input_qty   - units this step *consumes* per cycle
    • num_outputs - how many output ports / products to create
    • out_qty_N   - units produced per cycle on output port N  (dynamic)
    • out_name_N  - display label for output port N            (dynamic)
    • time        - seconds per cycle
    • machines    - (read-only display) calculated machine count
    """

    __identifier__ = "factory.nodes"
    NODE_NAME = "Production Step"

    def __init__(self):
        super().__init__()

        # flag to prevent recalculate() from running during loading
        self.loading = False 

        # ── editable inputs ────────────────────────────────────────────────

        self.input_widget = InputRowWidget(
            parent=self.view,
            name="input_widget",
        )
        self.add_custom_widget(self.input_widget, tab="widget")
        self.input_widget.onInputChange(self.recalculate)
        self.input_widget.onTimeChange(self.recalculate)

        # ── one input connector ───────────────────────────────────────────
        self.add_input("input", multi_input=True)

        # ── defaults ──────────────────────────────────────────────────────
        self.model.add_property("num_outputs", "0") # add hidden property to track how many output ports the node should have

        # ── output ports ─────────────────────────────────────────────────────────
        self.output_port_data = []   # store per-port data here

        # Seed with one output port + its qty property
        self.add_port()

        # Allow NodeGraphQt to delete output ports at runtime
        self.set_port_deletion_allowed(True)

    # ------------------------------------------------------------------
    # adding type hints for inherited methods
    # ------------------------------------------------------------------

    def get_input(self, port: int | str) -> Port | None:
        return super().get_input(port)
    
    def get_output(self, port: int | str) -> Port | None:
        return super().get_output(port)
    
    def input_ports(self) -> list[Port]:
        return super().input_ports()
    
    def output_ports(self) -> list[Port]:
        return super().output_ports()

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _safe_float(self, prop: str, default: float = 1.0) -> float:
        try:
            val = float(self.get_property(prop))
            return val if val > 0 else default
        except (ValueError, TypeError):
            return default

    def _safe_int(self, prop: str, default: int = 1, minimum: int = 0) -> int:
        try:
            val = int(float(self.get_property(prop)))
            return max(val, minimum)
        except (ValueError, TypeError):
            return default

    def _out_name_key(self, idx: int) -> str:
        return f"out_name_{idx}"
    
    def _out_port_name(self, idx: int) -> str:
        if idx < len(self.output_port_data):
            return self.output_port_data[idx]["name"]
        return f"output_{idx}"
    
    def _add_output_port(self, port_name: str, multi_output: bool = False) -> None:
        self.add_output(port_name, multi_output=multi_output)
        self.output_port_data.append({"name": port_name})
    
    def _port_to_dict(self, port: Port) -> dict:
        return {
            'name': port.name(),
            'multi_connection': port.multi_connection(),
            'display_name': port.model.display_name,
            'locked': port.model.locked
        }
    
    def get_output_widget(self, key: int | str) -> OutputRowWidget | None:
        if isinstance(key, int):
            key = self._out_name_key(key)
        widget = self.get_widget(key)
        if isinstance(widget, OutputRowWidget):
            return widget
        return None
    
    def add_port(self) -> None:
        """Add a new output port to the node."""
        i = len(self.output_ports())
        port_name = self._out_port_name(i)
        name_key  = self._out_name_key(i)

        num_outputs = self._safe_int("num_outputs", 1)
        self.set_property("num_outputs", str(num_outputs + 1))

        self._add_output_port(port_name)

        label = ""
        if i == 0:
            label = "Out name        Qty      Ideal      Real    "

        if self.get_output_widget(name_key) is None:
            output = OutputRowWidget(
                parent=self.view,
                name=name_key,
                label=label,
            )
            self.add_custom_widget(output, tab="Properties")
            self._model._custom_prop.pop(name_key, None)  # remove the property auto-added by add_custom_widget
            output.onNameChange(self._sync_output_port_labels)
            output.onOutputChange(self.recalculate)
        else:
            self.show_widget(name_key)
        
        self.update()
        self.recalculate()
    
    def remove_port(self) -> None:
        """Removes the last output port and its properties."""
        i = len(self.output_ports()) - 1
        if i == 0:
            return

        num_outputs = self._safe_int("num_outputs", 1)
        if num_outputs > 1:
            self.set_property("num_outputs", str(num_outputs - 1))

        port = self.get_output(-1)
        if port:
            for cp in list(port.connected_ports()):
                port.disconnect_from(cp)
            self.delete_output(port.name())
        
        self.output_port_data.pop()

        # hide the custom widget for this output's properties
        name_key = self._out_name_key(i)
        self.hide_widget(name_key)
        
        self.update()

    def _sync_output_port_labels(self) -> None:
        """Keep output port display names in sync with their corresponding property values."""

        output_port_qty = len(self.output_ports())

        update_ports = False

        for i in range(output_port_qty):
            port_name = self._out_port_name(i)
            name_key  = self._out_name_key(i)
            port = self.get_output(i)

            output_widget = self.get_output_widget(name_key)
            label = output_widget.get_output_name()

            if port and port.name() != label:
                self.output_port_data[i]["name"] = label
                update_ports = True
        
        if not update_ports:
            return
        
        connected_ports = {}

        output_port_qty = len(self.output_ports())

        for i in range(output_port_qty):
            port_name = self._out_port_name(i)
            name_key  = self._out_name_key(i)
            port = self.get_output(i)

            if port:
                connected_ports[i] = port.connected_ports()

        try:
            input_port_connections = self.get_input(0).connected_ports() if self.get_input(0) else []
        except Exception as e:
            print(f"Error getting connected ports for input of node {self.name()}: {e}")
            raise e

        port_data = {
            'input_ports': [
                self._port_to_dict(p) for p in self.input_ports()
            ],
            'output_ports': [
                self._port_to_dict(p) for p in self.output_ports()
            ]
        }

        for idx, p in enumerate(self.output_port_data):
            port_data["output_ports"][idx]["name"] = p["name"]


        for port in self.input_ports() + self.output_ports():
            if port:
                try:
                    port.clear_connections()
                except AttributeError:
                    pass

        self.set_port_deletion_allowed(True)
        self.set_ports(port_data)

        for cp in input_port_connections:
            self.get_input(0).connect_to(cp)
            pass

        for idx, value in connected_ports.items():
            port_name = self._out_port_name(idx)
            port = self.get_output(port_name)

            if port:
                for cp in value:
                    port.connect_to(cp)
                    pass

    # ------------------------------------------------------------------
    # core calculation
    # ------------------------------------------------------------------

    def increment_counter(self) -> None:
        with open("counter.txt", "r+") as f:
            count = int(f.read().strip() or "0")
            count += 1
            f.seek(0)
            f.write(str(count))
            f.truncate()

    def recalculate(self) -> dict:
        """
        Pull the upstream output rate from any connected input port,
        compute machines_needed, then return a dict of per-port rates:
            { port_name: units_per_sec }

        Downstream nodes call upstream_node.recalculate() and look up
        the rate for whichever port name they are connected to.
        """
        if self.loading:
            return {}

        input_qty = self.input_widget.get_input_qty()
        time_val  = self.input_widget.get_time()
        num_out   = self._safe_int("num_outputs",  1)

        # ── upstream rate ──────────────────────────────────────────────
        upstream_rate = self._get_upstream_rate()

        if upstream_rate is None:
            # nothing connected - standalone, assume 1 machine
            machines = 1
            min_machines = 1
        else:
            consumption_per_machine = input_qty / time_val
            if consumption_per_machine > 0:
                machines = upstream_rate / consumption_per_machine
                min_machines = math.ceil(machines)
            else:
                min_machines = 0
            min_machines = max(min_machines, 1)
        self.input_widget.set_machines(f"{min_machines} ({machines:.2f})")

        # ── per-port output rates ──────────────────────────────────────
        rates = {}

        if self.NODE_NAME == "Greenhouse":
            self.increment_counter()
        
        for i in range(num_out):
            port_name = self._out_port_name(i)
            output_widget = self.get_output_widget(i)
            try:
                if output_widget is None:
                    continue
                out_qty = output_widget.get_output_qty()
                ideal_rate      = (min_machines * out_qty) / time_val
                real_rate       = (machines * out_qty) / time_val
                output_widget.set_output_ideal(ideal_rate)
                output_widget.set_output_real(real_rate)
                rates[port_name] = real_rate
            except ValueError:
                output_widget.set_output_ideal(0)
                output_widget.set_output_real(0)
                rates[port_name] = 0.0
            
            port = self.get_output(i)
            if port:
                for cp in port.connected_ports():
                    downstream_node = cp.node()
                    if isinstance(downstream_node, ProductionNode):
                        downstream_node.recalculate()

        return rates
    

    def _get_upstream_rate(self) -> float | None:
        """
        Return the *sum* of output rates (units/sec) from all nodes connected
        to our input port, or None if nothing is connected.

        Each upstream port is looked up by name in the rates dict returned
        by that node's recalculate(), so multi-output upstreams are handled
        correctly: only the connected port's rate is counted.
        """
        input_port = self.input(0)
        if input_port is None:
            return None
        connected = input_port.connected_ports()
        if not connected:
            return None

        total = 0.0
        for upstream_port in connected:
            upstream_node = upstream_port.node()
            if isinstance(upstream_node, ProductionNode):
                # get index of the output port we're connected to on the upstream node
                port_index = upstream_node.output_ports().index(upstream_port)
                rate = upstream_node.get_output_widget(port_index).get_output_real()
                total += float(rate)
        return total
