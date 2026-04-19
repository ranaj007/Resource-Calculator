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

import math
from NodeGraphQt import BaseNode, Port

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

        # ── add/remove ports ───────────────────────────────────────────────
        self.add_button("add_output", "+1 Output", tab="Properties")
        self.add_button("remove_output", "-1 Output", tab="Properties")

        btn = self.get_widget('add_output')
        btn.value_changed.connect(self.add_port)

        btn = self.get_widget('remove_output')
        btn.value_changed.connect(self.remove_port)

        # ── editable inputs ────────────────────────────────────────────────
        self.add_text_input("input_qty",   "Input Qty",  tab="Properties")
        self.add_text_input("time",        "Time (s)",   tab="Properties")

        # ── read-only display ──────────────────────────────────────────────
        self.add_text_input("machines",    "Machines",   tab="Properties")

        # ── one input connector ───────────────────────────────────────────
        self.add_input("input", multi_input=True)

        # ── defaults ──────────────────────────────────────────────────────
        self.model.add_property("num_outputs", "1") # add hidden property to track how many output ports the node should have

        self.set_property("input_qty",   "1")
        self.set_property("time",        "1")
        self.set_property("machines",    "—")

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

    def _safe_int(self, prop: str, default: int = 1, minimum: int = 1) -> int:
        try:
            val = int(float(self.get_property(prop)))
            return max(val, minimum)
        except (ValueError, TypeError):
            return default

    def _out_qty_key(self, idx: int) -> str:
        return f"out_qty_{idx}"

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
    
    
    def add_port(self) -> None:
        """Add a new output port to the node."""
        i = len(self.output_ports())
        port_name = self._out_port_name(i)
        qty_key   = self._out_qty_key(i)
        name_key  = self._out_name_key(i)

        self._add_output_port(port_name)

        if self.get_property(name_key) is None:
            self.add_text_input(name_key, f"Out Name [{i}]", tab="Properties")
            self.set_property(name_key, f"output_{i}")
        else:
            self.get_widget(name_key).setVisible(True)

        if self.get_property(qty_key) is None:
            self.add_text_input(qty_key, f"Out Qty [{i}]", tab="Properties")
            self.set_property(qty_key, "1")
        else:
            self.get_widget(qty_key).setVisible(True)
        
        self.update()

    
    def remove_port(self) -> None:
        """Removes the last output port and hides its properties."""
        i = len(self.output_ports()) - 1
        qty_key  = self._out_qty_key(i)
        name_key = self._out_name_key(i)

        port = self.get_output(-1)
        if port:
            for cp in list(port.connected_ports()):
                port.disconnect_from(cp)
            self.delete_output(port.name())
        
        self.output_port_data.pop()
        
        # hide the properties but keep them around so values are remembered if user adds ports again
        if self.get_property(name_key) is not None:
            self.get_widget(name_key).setVisible(False)
        if self.get_property(qty_key) is not None:
            self.get_widget(qty_key).setVisible(False)
        
        self.update()


    def _sync_output_port_labels(self) -> None:
        """Keep output port display names in sync with their corresponding property values."""

        output_port_qty = len(self.output_ports())

        update_ports = False

        for i in range(output_port_qty):
            port_name = self._out_port_name(i)
            name_key  = self._out_name_key(i)
            port = self.get_output(i)

            label = self.get_property(name_key)

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

    def recalculate(self) -> dict:
        """
        Pull the upstream output rate from any connected input port,
        compute machines_needed, then return a dict of per-port rates:
            { port_name: units_per_sec }

        Downstream nodes call upstream_node.recalculate() and look up
        the rate for whichever port name they are connected to.
        """
        input_qty = self._safe_float("input_qty", 1.0)
        time_val  = self._safe_float("time",      1.0)
        num_out   = self._safe_int("num_outputs",  1)

        # ── upstream rate ──────────────────────────────────────────────
        upstream_rate = self._get_upstream_rate()

        if upstream_rate is None:
            # nothing connected - standalone, assume 1 machine
            machines = 1
            self.set_property("machines", f"{machines}  (standalone)")
        else:
            consumption_per_machine = input_qty / time_val
            if consumption_per_machine > 0:
                machines = math.ceil(upstream_rate / consumption_per_machine)
            else:
                machines = 0
            machines = max(machines, 1)
            self.set_property("machines", str(machines))

        # ── per-port output rates ──────────────────────────────────────
        rates = {}
        for i in range(num_out):
            qty_key   = self._out_qty_key(i)
            out_qty   = self._safe_float(qty_key, 1.0)
            rate      = (machines * out_qty) / time_val
            port_name = self._out_port_name(i)
            rates[port_name] = rate

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
                upstream_rates = upstream_node.recalculate()
                # pull the rate for the specific port wired to us
                rate = upstream_rates.get(upstream_port.name(), 0.0)
                total += rate
        return total
