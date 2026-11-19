import unittest
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.database import init_db
from database.models import ClassificationRuleModel
from backend.classification.classifier import TrafficClassifier
from app import create_app

class TestTrafficClassification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.classifier = TrafficClassifier()
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_high_priority_voip_classification(self):
        """VoIP SIP (5060) and RTP (10024) must be classified as HIGH priority."""
        prio, app, _ = self.classifier.classify_packet("UDP", 5060, 5060, 200)
        self.assertEqual(prio, "HIGH")
        self.assertIn("VoIP", app)

        prio_rtp, app_rtp, _ = self.classifier.classify_packet("UDP", 10024, 10024, 180)
        self.assertEqual(prio_rtp, "HIGH")

    def test_high_priority_video_conferencing(self):
        """Zoom / WebRTC media streams must be classified as HIGH priority."""
        prio, app, _ = self.classifier.classify_packet("UDP", 8801, 8801, 1200)
        self.assertEqual(prio, "HIGH")
        self.assertIn("Video", app)

    def test_high_priority_icmp(self):
        """ICMP Echo diagnostics must be classified as HIGH priority."""
        prio, app, _ = self.classifier.classify_packet("ICMP", 0, 0, 64)
        self.assertEqual(prio, "HIGH")

    def test_medium_priority_web_and_dns(self):
        """DNS (53), HTTP (80), and HTTPS (443) must be classified as MEDIUM priority."""
        prio_dns, app_dns, _ = self.classifier.classify_packet("UDP", 53, 50000, 72)
        self.assertEqual(prio_dns, "MEDIUM")

        prio_http, app_http, _ = self.classifier.classify_packet("TCP", 80, 50000, 600)
        self.assertEqual(prio_http, "MEDIUM")

        prio_https, app_https, _ = self.classifier.classify_packet("TCP", 443, 50000, 1200)
        self.assertEqual(prio_https, "MEDIUM")

    def test_low_priority_bulk_and_p2p(self):
        """FTP (21) and BitTorrent (6881) must be classified as LOW priority."""
        prio_ftp, app_ftp, _ = self.classifier.classify_packet("TCP", 21, 40000, 1460)
        self.assertEqual(prio_ftp, "LOW")

        prio_p2p, app_p2p, _ = self.classifier.classify_packet("TCP", 6881, 40000, 1460)
        self.assertEqual(prio_p2p, "LOW")

    def test_custom_rule_lifecycle(self):
        """Test adding a dynamic rule, matching traffic against it, and deleting it."""
        rule_id = ClassificationRuleModel.insert(
            name="Test Gaming UDP",
            protocol="UDP",
            port_range="27015",
            priority="HIGH",
            app_name="Source Game Server",
            description="Low-latency multiplayer gaming"
        )
        self.classifier.reload_rules()

        prio, app, _ = self.classifier.classify_packet("UDP", 27015, 50000, 120)
        self.assertEqual(prio, "HIGH")
        self.assertEqual(app, "Source Game Server")

        # Cleanup
        ClassificationRuleModel.delete(rule_id)
        self.classifier.reload_rules()

    def test_classification_api(self):
        """Test /api/classification/rules and /api/classification/stats."""
        res_rules = self.client.get("/api/classification/rules")
        self.assertEqual(res_rules.status_code, 200)
        self.assertTrue(res_rules.get_json()["success"])

        res_stats = self.client.get("/api/classification/stats")
        self.assertEqual(res_stats.status_code, 200)
        self.assertTrue(res_stats.get_json()["success"])

if __name__ == "__main__":
    unittest.main()
