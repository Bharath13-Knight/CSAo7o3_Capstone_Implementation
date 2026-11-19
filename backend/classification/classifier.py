import logging
from backend.classification.rules import DEFAULT_PORT_CLASSIFICATIONS
from database.models import ClassificationRuleModel

logger = logging.getLogger(__name__)

class TrafficClassifier:
    """
    Intelligent packet and flow classification engine.
    Categorizes traffic into HIGH, MEDIUM, and LOW priority based on:
    - Protocol (ICMP, TCP, UDP, DNS, HTTP)
    - Source and Destination Ports
    - User-configured dynamic database rules
    - Packet metadata and payload heuristics (without decrypting payload)
    """

    def __init__(self):
        self._cached_db_rules = []
        self.reload_rules()

    def reload_rules(self):
        """Reload active classification rules from the SQLite database."""
        try:
            self._cached_db_rules = ClassificationRuleModel.get_all()
        except Exception as e:
            logger.warning("Could not load rules from DB, using defaults: %s", e)
            self._cached_db_rules = []

    def classify_packet(self, protocol, src_port, dst_port, length, payload_sample=b""):
        """
        Classifies an individual packet into (priority, application_name, info).
        Returns a tuple: ('HIGH'|'MEDIUM'|'LOW', application_name, description)
        """
        proto_upper = str(protocol).upper()

        # 1. Check protocol-specific overrides
        if proto_upper == "ICMP":
            return ("HIGH", "ICMP Diagnostics", "Low-latency network echo probe")

        # 2. Check dynamic user-defined database rules
        for rule in self._cached_db_rules:
            if not rule.get("is_active", 1):
                continue
            if rule["protocol"] != "ANY" and rule["protocol"].upper() != proto_upper:
                continue
            
            # Check port ranges
            port_range = rule.get("port_range", "")
            if port_range and self._match_port_range(src_port, dst_port, port_range):
                return (rule["priority"], rule["app_name"], rule.get("description", "Matched custom rule"))

        # 3. Check well-known port mapping
        ports_to_check = [p for p in (dst_port, src_port) if p is not None]
        for p in ports_to_check:
            if p in DEFAULT_PORT_CLASSIFICATIONS:
                info = DEFAULT_PORT_CLASSIFICATIONS[p]
                return (info["priority"], info["app"], f"Standard {info['category']} port {p}")

        # 4. Range heuristics (VoIP RTP typically 10000-20000 UDP)
        for p in ports_to_check:
            if proto_upper == "UDP" and 10000 <= p <= 20000:
                return ("HIGH", "VoIP (RTP Stream)", f"Real-time voice stream on UDP port {p}")
            if proto_upper == "TCP" and 6881 <= p <= 6889:
                return ("LOW", "BitTorrent P2P", f"Peer-to-peer file transfer port {p}")

        # 5. Packet size & protocol heuristic fallback
        if proto_upper == "UDP":
            if length < 300:
                return ("HIGH", "UDP Real-Time", "Small real-time UDP packet")
            else:
                return ("MEDIUM", "UDP Data", "Standard UDP datagram")

        if proto_upper == "TCP":
            if length > 1400:
                return ("LOW", "Bulk TCP Transfer", "Large MTU-sized data segment")
            elif length < 100:
                return ("MEDIUM", "TCP Control", "TCP handshake / ACK control packet")
            else:
                return ("MEDIUM", "General TCP", "Interactive application data")

        return ("MEDIUM", "General IP", "Standard IP traffic")

    def _match_port_range(self, src_port, dst_port, port_range_str):
        """Matches src or dst port against comma-separated or hyphenated port ranges (e.g., '5060,5061' or '10000-20000')."""
        ports = [p for p in (src_port, dst_port) if p is not None]
        for part in port_range_str.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                try:
                    start, end = part.split("-")
                    start, end = int(start), int(end)
                    if any(start <= p <= end for p in ports):
                        return True
                except ValueError:
                    continue
            else:
                try:
                    val = int(part)
                    if any(p == val for p in ports):
                        return True
                except ValueError:
                    continue
        return False
