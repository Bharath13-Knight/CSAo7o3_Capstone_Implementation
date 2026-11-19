import logging
from config import Config
from backend.monitoring.flow_aggregator import FlowAggregator
from backend.monitoring.traffic_generator import TrafficGenerator
from backend.monitoring.packet_sniffer import PacketSniffer
from backend.classification.classifier import TrafficClassifier
from database.models import PacketModel, SettingsModel

logger = logging.getLogger(__name__)

class MonitoringService:
    """Singleton service coordinating packet sniffing, generation, and aggregation."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MonitoringService, cls).__new__(cls)
            cls._instance._init_service()
        return cls._instance

    def _init_service(self):
        self.is_monitoring = False
        self.current_interface = Config.DEFAULT_INTERFACE
        self.current_mode = Config.DEFAULT_MONITORING_MODE
        self.classifier = TrafficClassifier()
        self.flow_aggregator = FlowAggregator()
        self.traffic_generator = TrafficGenerator(self.flow_aggregator, self.classifier)
        self.packet_sniffer = PacketSniffer(self.flow_aggregator, self.classifier)
        
        try:
            self.current_mode = SettingsModel.get("monitoring_mode", Config.DEFAULT_MONITORING_MODE)
        except Exception:
            self.current_mode = Config.DEFAULT_MONITORING_MODE

    def start_monitoring(self, mode=None, interface=None, rate=10):
        """Starts monitoring either in SIMULATION or LIVE mode."""
        if mode:
            self.current_mode = mode
            SettingsModel.set("monitoring_mode", mode)
        if interface:
            self.current_interface = interface

        if self.current_mode == "LIVE":
            success, msg = self.packet_sniffer.start(self.current_interface)
            if not success:
                logger.warning("Falling back to simulation mode: %s", msg)
                self.current_mode = "SIMULATION"
                self.traffic_generator.start(rate=rate)
                self.is_monitoring = True
                return {
                    "status": "RUNNING",
                    "mode": "SIMULATION",
                    "fallback": True,
                    "message": f"Live sniffing unavailable ({msg}). Running in high-fidelity SIMULATION mode."
                }
            self.is_monitoring = True
            return {"status": "RUNNING", "mode": "LIVE", "interface": self.current_interface, "message": msg}
        else:
            self.traffic_generator.start(rate=rate)
            self.is_monitoring = True
            return {"status": "RUNNING", "mode": "SIMULATION", "message": "Simulation traffic generator started."}

    def stop_monitoring(self):
        """Stops active monitoring."""
        self.traffic_generator.stop()
        self.packet_sniffer.stop()
        self.is_monitoring = False
        return {"status": "STOPPED", "message": "Monitoring stopped."}

    def clear_traffic(self):
        """Clears memory buffers and database packet logs."""
        self.flow_aggregator.clear()
        PacketModel.clear_all()
        return {"status": "CLEARED", "message": "Traffic buffers cleared."}

    def get_status(self):
        """Returns the current monitoring status."""
        return {
            "is_monitoring": self.is_monitoring,
            "mode": self.current_mode,
            "interface": self.current_interface,
            "scapy_supported": self.packet_sniffer.is_supported(),
            "metrics": self.flow_aggregator.get_live_metrics()
        }

    def get_packets(self, limit=50, protocol="ALL", priority="ALL", src_ip="", dst_ip=""):
        """Returns filtered recent packets."""
        # Check memory buffer first
        mem_packets = self.flow_aggregator.get_recent_packets(limit, protocol, priority, src_ip, dst_ip)
        if mem_packets:
            return mem_packets
        # Fall back to database query
        return PacketModel.get_recent(limit, protocol, priority, src_ip, dst_ip)
