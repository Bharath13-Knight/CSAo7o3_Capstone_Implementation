import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "network-qos-super-secret-key-2026")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", str(BASE_DIR / "database" / "network_qos.db"))
    REPORTS_DIR = os.environ.get("REPORTS_DIR", str(BASE_DIR / "reports"))
    
    # Network Topology Subnets Definition
    DEFAULT_SUBNETS = [
        {
            "id": "subnet-a",
            "name": "Subnet A (Engineering)",
            "cidr": "192.168.1.0/24",
            "gateway": "192.168.1.1",
            "vlan": 10,
            "status": "UP",
            "description": "High-traffic workstation subnet hosting VoIP and dev clients"
        },
        {
            "id": "subnet-b",
            "name": "Subnet B (Operations)",
            "cidr": "192.168.2.0/24",
            "gateway": "192.168.2.1",
            "vlan": 20,
            "status": "UP",
            "description": "Web browsing, business communication, and management traffic"
        },
        {
            "id": "subnet-c",
            "name": "Subnet C (Data Center & Servers)",
            "cidr": "192.168.3.0/24",
            "gateway": "192.168.3.1",
            "vlan": 30,
            "status": "UP",
            "description": "Backup servers, file repositories, and database replicas"
        }
    ]

    # Pre-configured Virtual Devices
    DEFAULT_DEVICES = [
        {"id": "pc1", "name": "PC1 (VoIP / Dev)", "ip": "192.168.1.10", "mac": "00:00:00:00:01:0A", "subnet_id": "subnet-a", "type": "Workstation", "status": "ONLINE"},
        {"id": "pc2", "name": "PC2 (Dev Station)", "ip": "192.168.1.20", "mac": "00:00:00:00:01:14", "subnet_id": "subnet-a", "type": "Workstation", "status": "ONLINE"},
        {"id": "pc3", "name": "PC3 (Operations)", "ip": "192.168.2.10", "mac": "00:00:00:00:02:0A", "subnet_id": "subnet-b", "type": "Workstation", "status": "ONLINE"},
        {"id": "pc4", "name": "PC4 (Management)", "ip": "192.168.2.20", "mac": "00:00:00:00:02:14", "subnet_id": "subnet-b", "type": "Workstation", "status": "ONLINE"},
        {"id": "pc5", "name": "PC5 (File Server)", "ip": "192.168.3.10", "mac": "00:00:00:00:03:0A", "subnet_id": "subnet-c", "type": "Server", "status": "ONLINE"},
        {"id": "pc6", "name": "PC6 (Backup Host)", "ip": "192.168.3.20", "mac": "00:00:00:00:03:14", "subnet_id": "subnet-c", "type": "Server", "status": "ONLINE"},
    ]

    # Core Router Configuration
    ROUTER_CONFIG = {
        "id": "router-1",
        "name": "Core Edge Router (R1)",
        "interfaces": [
            {"name": "eth1", "ip": "192.168.1.1", "subnet": "Subnet A", "status": "UP"},
            {"name": "eth2", "ip": "192.168.2.1", "subnet": "Subnet B", "status": "UP"},
            {"name": "eth3", "ip": "192.168.3.1", "subnet": "Subnet C", "status": "UP"},
            {"name": "eth0", "ip": "10.0.0.1", "subnet": "WAN/Internet", "status": "UP"}
        ]
    }

    # Monitoring Settings
    MONITORING_RATE_PACKETS_PER_SEC = 10
    MAX_PACKETS_IN_MEMORY = 500
    DEFAULT_MONITORING_MODE = "SIMULATION"  # "SIMULATION" or "LIVE"
    DEFAULT_INTERFACE = "eth0"
    
    # QoS Defaults
    TOTAL_BANDWIDTH_MBPS = 100.0
    HIGH_PRIORITY_BANDWIDTH_PERCENT = 55.0   # Voice, Video
    MEDIUM_PRIORITY_BANDWIDTH_PERCENT = 30.0 # Web, DNS
    LOW_PRIORITY_BANDWIDTH_PERCENT = 15.0    # FTP, Bulk

    # Server settings
    HOST = "127.0.0.1"
    PORT = 5000
    DEBUG = True
