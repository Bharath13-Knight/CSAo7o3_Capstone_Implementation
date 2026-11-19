import socket
import platform
import logging
from config import Config
from database.models import SubnetModel, DeviceModel

logger = logging.getLogger(__name__)

class TopologyManager:
    """Manages the 3-subnet network topology, virtual nodes, switches, router, and links."""

    def __init__(self):
        self.router_info = Config.ROUTER_CONFIG
        self.host_info = self._get_host_network_info()

    def _get_host_network_info(self):
        """Retrieve the actual host system information to clearly distinguish from virtual subnets."""
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
        except Exception:
            hostname = "localhost"
            ip = "127.0.0.1"
            
        return {
            "hostname": hostname,
            "host_os": f"{platform.system()} {platform.release()}",
            "host_ip": ip,
            "is_virtual_demonstration": True,
            "virtual_subnets_count": 3
        }

    def get_topology_data(self):
        """Returns the full node-link graph data structure for interactive visualization."""
        subnets = SubnetModel.get_all()
        devices = DeviceModel.get_all()

        nodes = []
        edges = []

        # 1. Add WAN / Internet Node
        nodes.append({
            "id": "wan",
            "label": "WAN / Internet\n10.0.0.0/8",
            "group": "wan",
            "type": "WAN Gateway",
            "ip": "10.0.0.1",
            "status": "UP",
            "shape": "diamond",
            "color": {"background": "#00E5FF", "border": "#00B4D8"}
        })

        # 2. Add Core Router (R1)
        nodes.append({
            "id": "router-1",
            "label": "Core Router (R1)\n(QoS Enforcer)",
            "group": "router",
            "type": "Router",
            "ip": "192.168.1.1 / 2.1 / 3.1",
            "status": "UP",
            "shape": "hexagon",
            "color": {"background": "#7209B7", "border": "#560BAD"},
            "interfaces": self.router_info["interfaces"]
        })

        edges.append({
            "from": "wan",
            "to": "router-1",
            "label": "WAN Link\n1 Gbps",
            "color": "#00E5FF",
            "dashes": True,
            "arrows": "to;from"
        })

        # 3. Add Switches for each subnet
        switch_map = {
            "subnet-a": {"id": "sw-a", "label": "Switch S1\n(VLAN 10)", "color": "#4361EE"},
            "subnet-b": {"id": "sw-b", "label": "Switch S2\n(VLAN 20)", "color": "#4CC9F0"},
            "subnet-c": {"id": "sw-c", "label": "Switch S3\n(VLAN 30)", "color": "#F72585"}
        }

        for subnet in subnets:
            s_id = subnet["id"]
            sw = switch_map.get(s_id, {"id": f"sw-{s_id}", "label": f"Switch {s_id}", "color": "#4895EF"})
            
            # Switch Node
            nodes.append({
                "id": sw["id"],
                "label": sw["label"],
                "group": "switch",
                "type": "Switch",
                "subnet_id": s_id,
                "status": subnet.get("status", "UP"),
                "shape": "box",
                "color": {"background": "#1E293B", "border": sw["color"]}
            })

            # Edge from Router to Switch
            gw = subnet["gateway"]
            edges.append({
                "from": "router-1",
                "to": sw["id"],
                "label": f"Trunk {gw}\n100 Mbps",
                "color": sw["color"],
                "width": 3,
                "arrows": "to;from"
            })

        # 4. Add Devices connected to their Subnet Switch
        for dev in devices:
            sw_id = switch_map.get(dev["subnet_id"], {}).get("id", "sw-a")
            is_server = "Server" in dev["type"]
            nodes.append({
                "id": dev["id"],
                "label": f"{dev['name']}\n{dev['ip']}",
                "group": "server" if is_server else "host",
                "type": dev["type"],
                "ip": dev["ip"],
                "mac": dev["mac"],
                "subnet_id": dev["subnet_id"],
                "status": dev["status"],
                "shape": "dot",
                "color": {"background": "#10B981" if dev["status"] == "ONLINE" else "#EF4444", "border": "#FFFFFF"}
            })

            edges.append({
                "from": sw_id,
                "to": dev["id"],
                "label": "Access 100M",
                "color": "#64748B",
                "width": 1.5
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "subnets": subnets,
            "devices": devices,
            "router": self.router_info,
            "host_environment": self.host_info
        }

    def get_subnet_status(self):
        """Returns real-time status and telemetry for each subnet."""
        subnets = SubnetModel.get_all()
        devices = DeviceModel.get_all()
        
        result = []
        for s in subnets:
            s_devs = [d for d in devices if d["subnet_id"] == s["id"]]
            online_count = sum(1 for d in s_devs if d["status"] == "ONLINE")
            result.append({
                "id": s["id"],
                "name": s["name"],
                "cidr": s["cidr"],
                "gateway": s["gateway"],
                "vlan": s["vlan"],
                "status": s["status"],
                "description": s["description"],
                "total_devices": len(s_devs),
                "online_devices": online_count,
                "devices": s_devs
            })
        return result
