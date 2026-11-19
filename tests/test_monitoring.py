import unittest
import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import Config
from database.database import init_db
from database.models import PacketModel
from backend.monitoring.flow_aggregator import FlowAggregator
from backend.monitoring.traffic_generator import TrafficGenerator
from backend.classification.classifier import TrafficClassifier
from app import create_app

class TestTrafficMonitoring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def setUp(self):
        self.classifier = TrafficClassifier()
        self.aggregator = FlowAggregator()

    def test_flow_aggregator_packet_recording(self):
        """Test that packets are accurately counted and aggregated."""
        pkt = {
            "session_id": "test-sess",
            "timestamp": "2026-11-19 10:00:00",
            "src_ip": "192.168.1.10",
            "dst_ip": "192.168.2.10",
            "src_port": 10024,
            "dst_port": 10024,
            "protocol": "UDP",
            "length": 200,
            "priority": "HIGH",
            "application": "VoIP (RTP Audio)",
            "info": "Test voice frame",
            "mode": "SIMULATION"
        }
        self.aggregator.record_packet(pkt)
        metrics = self.aggregator.get_live_metrics()
        
        self.assertEqual(metrics["total_packets"], 1)
        self.assertEqual(metrics["total_bytes"], 200)
        self.assertEqual(metrics["priority_counts"]["HIGH"], 1)
        self.assertEqual(metrics["protocol_counts"]["UDP"], 1)

    def test_packet_database_persistence_and_filtering(self):
        """Test storing packet in SQLite and querying with protocol and priority filters."""
        PacketModel.insert(
            session_id="test-db",
            src_ip="192.168.1.20",
            dst_ip="192.168.3.10",
            src_port=80,
            dst_port=54321,
            protocol="HTTP",
            length=800,
            priority="MEDIUM",
            application="HTTP Web",
            info="Test HTTP payload",
            mode="SIMULATION"
        )
        
        # Query with protocol filter
        packets = PacketModel.get_recent(limit=10, protocol="HTTP")
        self.assertTrue(len(packets) >= 1)
        self.assertEqual(packets[0]["protocol"], "HTTP")
        self.assertEqual(packets[0]["priority"], "MEDIUM")

    def test_traffic_generator_batch(self):
        """Test TrafficGenerator generates valid cross-subnet packet flows."""
        generator = TrafficGenerator(self.aggregator, self.classifier)
        generator.start(rate=20)
        import time
        time.sleep(0.5)
        generator.stop()

        metrics = self.aggregator.get_live_metrics()
        self.assertGreater(metrics["total_packets"], 0)
        self.assertGreater(metrics["total_bytes"], 0)

    def test_monitoring_api_endpoints(self):
        """Test /api/monitoring/status and packet retrieval APIs."""
        res = self.client.get("/api/monitoring/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("metrics", data["status"])

        res_packets = self.client.get("/api/monitoring/packets?limit=5")
        self.assertEqual(res_packets.status_code, 200)
        data_p = res_packets.get_json()
        self.assertTrue(data_p["success"])
        self.assertIsInstance(data_p["packets"], list)

if __name__ == "__main__":
    unittest.main()
