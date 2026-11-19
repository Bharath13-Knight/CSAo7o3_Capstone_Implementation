import time
import random
import threading
import uuid
import logging
from database.models import PacketModel

logger = logging.getLogger(__name__)

class TrafficGenerator:
    """
    High-fidelity traffic simulator that models cross-subnet network conversations
    between Subnet A, Subnet B, Subnet C, and WAN.
    """

    def __init__(self, flow_aggregator, classifier):
        self.flow_aggregator = flow_aggregator
        self.classifier = classifier
        self.is_running = False
        self._thread = None
        self.packets_per_sec = 10
        self.session_id = str(uuid.uuid4())[:8]

    def start(self, rate=10):
        """Starts the multi-subnet simulation loop."""
        if self.is_running:
            return
        self.is_running = True
        self.packets_per_sec = rate
        self.session_id = f"sim-{str(uuid.uuid4())[:8]}"
        self._thread = threading.Thread(target=self._run_simulation, daemon=True)
        self._thread.start()
        logger.info("Traffic generator started in session %s with rate %d pps", self.session_id, self.packets_per_sec)

    def stop(self):
        """Stops the traffic simulator."""
        self.is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        logger.info("Traffic generator stopped")

    def _run_simulation(self):
        """Generates realistic bursts of network packets across subnets."""
        # Weighted stream templates
        streams = [
            # 1. VoIP Voice Stream (High Priority)
            {
                "weight": 25,
                "protocol": "UDP",
                "src_ip": "192.168.1.10", # PC1
                "dst_ip": "192.168.2.10", # PC3
                "src_port": 10024,
                "dst_port": 10024,
                "size_range": (160, 240),
                "app": "VoIP (RTP Audio)",
                "info": "G.711 VoIP audio payload frame seq="
            },
            # 2. Video Conference (High Priority)
            {
                "weight": 20,
                "protocol": "UDP",
                "src_ip": "192.168.1.20", # PC2
                "dst_ip": "192.168.2.20", # PC4
                "src_port": 8801,
                "dst_port": 8801,
                "size_range": (850, 1400),
                "app": "Video Conference",
                "info": "WebRTC H.264 video RTP slice"
            },
            # 3. HTTPS Web & Cloud API (Medium Priority)
            {
                "weight": 20,
                "protocol": "TCP",
                "src_ip": "192.168.2.10", # PC3
                "dst_ip": "10.0.0.1",     # WAN Gateway
                "src_port": random.randint(49152, 65535),
                "dst_port": 443,
                "size_range": (400, 1450),
                "app": "HTTPS Secure Web",
                "info": "TLS Application Data (Encrypted metadata only)"
            },
            # 4. DNS Query & Response (Medium Priority)
            {
                "weight": 10,
                "protocol": "UDP",
                "src_ip": "192.168.1.10", # PC1
                "dst_ip": "192.168.1.1",  # Gateway
                "src_port": random.randint(50000, 60000),
                "dst_port": 53,
                "size_range": (68, 128),
                "app": "DNS Query",
                "info": "Standard query 0x7a3b A corp.intranet"
            },
            # 5. FTP / Database Sync Bulk Transfer (Low Priority)
            {
                "weight": 20,
                "protocol": "TCP",
                "src_ip": "192.168.3.20", # PC6 (Backup)
                "dst_ip": "192.168.3.10", # PC5 (Server)
                "src_port": 21,
                "dst_port": random.randint(40000, 50000),
                "size_range": (1420, 1514),
                "app": "FTP Bulk Transfer",
                "info": "Bulk data chunk [PSH, ACK] seq=18492"
            },
            # 6. ICMP Diagnostics (High Priority)
            {
                "weight": 5,
                "protocol": "ICMP",
                "src_ip": "192.168.1.20", # PC2
                "dst_ip": "192.168.3.10", # PC5
                "src_port": 0,
                "dst_port": 0,
                "size_range": (64, 84),
                "app": "ICMP Diagnostics",
                "info": "Echo (ping) request id=0x0001 seq=4"
            }
        ]

        # Flatten weights for fast random choice
        population = []
        for s in streams:
            population.extend([s] * s["weight"])

        seq_counter = 0

        while self.is_running:
            stream = random.choice(population)
            seq_counter += 1
            
            length = random.randint(*stream["size_range"])
            src_port = stream["src_port"] if stream["src_port"] != 0 else None
            dst_port = stream["dst_port"] if stream["dst_port"] != 0 else None

            # Two-way conversation: 40% chance to flip source & destination
            if random.random() < 0.4 and stream["protocol"] != "ICMP":
                src_ip, dst_ip = stream["dst_ip"], stream["src_ip"]
                src_p, dst_p = dst_port, src_port
            else:
                src_ip, dst_ip = stream["src_ip"], stream["dst_ip"]
                src_p, dst_p = src_port, dst_port

            # Classify packet
            priority, app_name, desc = self.classifier.classify_packet(
                stream["protocol"], src_p, dst_p, length
            )

            info_str = f"{stream['info']} #{seq_counter}"

            packet_dict = {
                "session_id": self.session_id,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "src_port": src_p,
                "dst_port": dst_p,
                "protocol": stream["protocol"],
                "length": length,
                "priority": priority,
                "application": app_name,
                "info": info_str,
                "mode": "SIMULATION"
            }

            # Update live aggregation
            self.flow_aggregator.record_packet(packet_dict)

            # Periodically persist packets to DB (sample 1 in 2 to keep DB performant)
            if seq_counter % 2 == 0:
                try:
                    PacketModel.insert(
                        session_id=self.session_id,
                        src_ip=src_ip,
                        dst_ip=dst_ip,
                        src_port=src_p,
                        dst_port=dst_p,
                        protocol=stream["protocol"],
                        length=length,
                        priority=priority,
                        application=app_name,
                        info=info_str,
                        mode="SIMULATION"
                    )
                except Exception as e:
                    logger.debug("Failed saving packet to DB: %s", e)

            # Sleep to match packet generation rate
            sleep_time = max(0.01, 1.0 / max(1, self.packets_per_sec))
            # Jitter sleep time slightly for realistic inter-arrival times (Poisson-like)
            jittered_sleep = random.uniform(sleep_time * 0.7, sleep_time * 1.3)
            time.sleep(jittered_sleep)
