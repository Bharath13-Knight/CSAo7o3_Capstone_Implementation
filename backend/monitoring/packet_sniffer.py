import time
import threading
import uuid
import logging
from config import Config
from database.models import PacketModel

logger = logging.getLogger(__name__)

# Check Scapy availability
try:
    from scapy.all import sniff, IP, TCP, UDP, ICMP, DNS
    SCAPY_AVAILABLE = True
except Exception as e:
    SCAPY_AVAILABLE = False
    logger.warning("Scapy live sniffer unavailable: %s", e)

class PacketSniffer:
    """
    Live packet capture engine powered by Scapy.
    Captures raw packets, extracts IP/Transport metadata, inspects flow protocols,
    and classifies packets without decrypting encrypted payloads.
    """

    def __init__(self, flow_aggregator, classifier):
        self.flow_aggregator = flow_aggregator
        self.classifier = classifier
        self.is_running = False
        self._thread = None
        self.interface = Config.DEFAULT_INTERFACE
        self.session_id = str(uuid.uuid4())[:8]
        self.error_message = None

    def is_supported(self):
        """Returns True if Scapy is installed and capable of sniffing."""
        return SCAPY_AVAILABLE

    def start(self, interface=None):
        """Starts live packet capture in a background thread."""
        if self.is_running:
            return True, "Sniffer already running"

        if not SCAPY_AVAILABLE:
            return False, "Scapy is not installed or pcap library is missing"

        if interface:
            self.interface = interface

        self.is_running = True
        self.error_message = None
        self.session_id = f"live-{str(uuid.uuid4())[:8]}"
        self._thread = threading.Thread(target=self._run_sniff, daemon=True)
        self._thread.start()
        logger.info("Live packet capture started on interface %s (session %s)", self.interface, self.session_id)
        return True, f"Capture started on {self.interface}"

    def stop(self):
        """Stops live packet capture."""
        self.is_running = False
        logger.info("Live packet capture stopped")

    def _run_sniff(self):
        """Internal sniffing loop using Scapy."""
        try:
            sniff(
                prn=self._process_scapy_packet,
                stop_filter=lambda p: not self.is_running,
                store=False
            )
        except Exception as e:
            logger.error("Live sniffing error: %s", e)
            self.error_message = str(e)
            self.is_running = False

    def _process_scapy_packet(self, packet):
        """Callback to parse each captured Scapy packet."""
        if not self.is_running:
            return

        try:
            if not packet.haslayer(IP):
                return

            ip_layer = packet.getlayer(IP)
            src_ip = ip_layer.src
            dst_ip = ip_layer.dst
            length = len(packet)
            
            src_port = None
            dst_port = None
            protocol = "OTHER"
            info = ""

            if packet.haslayer(TCP):
                protocol = "TCP"
                tcp = packet.getlayer(TCP)
                src_port = tcp.sport
                dst_port = tcp.dport
                flags = tcp.sprintf('%TCP.flags%')
                
                # Check for HTTP
                if dst_port == 80 or src_port == 80:
                    protocol = "HTTP"
                    info = f"HTTP Traffic [{flags}]"
                elif dst_port == 443 or src_port == 443:
                    info = f"TLS Encrypted Data [{flags}]"
                else:
                    info = f"TCP Segment [{flags}] seq={tcp.seq}"

            elif packet.haslayer(UDP):
                protocol = "UDP"
                udp = packet.getlayer(UDP)
                src_port = udp.sport
                dst_port = udp.dport
                
                if packet.haslayer(DNS):
                    protocol = "DNS"
                    info = "DNS Query / Response"
                elif dst_port == 53 or src_port == 53:
                    protocol = "DNS"
                    info = "DNS Transport"
                elif dst_port in (5060, 5061) or src_port in (5060, 5061):
                    info = "SIP Signaling"
                else:
                    info = f"UDP Datagram len={udp.len}"

            elif packet.haslayer(ICMP):
                protocol = "ICMP"
                icmp = packet.getlayer(ICMP)
                info = f"ICMP Type={icmp.type} Code={icmp.code}"

            # Priority classification
            priority, app_name, desc = self.classifier.classify_packet(
                protocol, src_port, dst_port, length
            )

            packet_dict = {
                "session_id": self.session_id,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "src_port": src_port,
                "dst_port": dst_port,
                "protocol": protocol,
                "length": length,
                "priority": priority,
                "application": app_name,
                "info": info or desc,
                "mode": "LIVE"
            }

            self.flow_aggregator.record_packet(packet_dict)

            # Persist to database
            try:
                PacketModel.insert(
                    session_id=self.session_id,
                    src_ip=src_ip,
                    dst_ip=dst_ip,
                    src_port=src_port,
                    dst_port=dst_port,
                    protocol=protocol,
                    length=length,
                    priority=priority,
                    application=app_name,
                    info=info or desc,
                    mode="LIVE"
                )
            except Exception as e:
                logger.debug("Failed saving live packet to DB: %s", e)

        except Exception as e:
            logger.debug("Packet parsing error: %s", e)
