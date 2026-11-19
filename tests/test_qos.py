import unittest
import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.database import init_db
from database.models import SubnetModel, DeviceModel
from backend.network.ping_utility import PingUtility
from backend.qos.tc_manager import TCManager
from backend.qos.qos_engine import QoSEngine
from backend.evaluation.evaluator import PerformanceEvaluator
from app import create_app

class TestQoSAndTopology(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_three_subnets_and_devices_configuration(self):
        """Verify the 3 required subnets and 6 devices are seeded properly."""
        subnets = SubnetModel.get_all()
        self.assertEqual(len(subnets), 3)

        sub_ids = [s["id"] for s in subnets]
        self.assertIn("subnet-a", sub_ids)
        self.assertIn("subnet-b", sub_ids)
        self.assertIn("subnet-c", sub_ids)

        devices = DeviceModel.get_all()
        self.assertEqual(len(devices), 6)
        ips = [d["ip"] for d in devices]
        self.assertIn("192.168.1.10", ips) # PC1
        self.assertIn("192.168.1.20", ips) # PC2
        self.assertIn("192.168.2.10", ips) # PC3
        self.assertIn("192.168.2.20", ips) # PC4
        self.assertIn("192.168.3.10", ips) # PC5
        self.assertIn("192.168.3.20", ips) # PC6

    def test_inter_subnet_virtual_ping_routing(self):
        """Verify routing and hop path between PC1 (Subnet A) and PC5 (Subnet C)."""
        res = PingUtility.ping_test("192.168.1.10", "192.168.3.10", count=3)
        self.assertEqual(res["type"], "VIRTUAL_TOPOLOGY_PING")
        self.assertFalse(res["same_subnet"])
        self.assertIn("Core Router R1 (Default Gateway)", res["hop_path"])
        self.assertEqual(res["packets_sent"], 3)
        self.assertEqual(res["packets_received"], 3)
        self.assertGreater(res["avg_rtt_ms"], 0)

    def test_tc_manager_command_generation(self):
        """Verify generation of Linux Traffic Control (tc) HTB and PRIO commands."""
        tc = TCManager(interface="eth0")
        cmds = tc.generate_tc_commands("eth0", total_bw=100.0, high_pct=55.0, med_pct=30.0, low_pct=15.0)
        
        cmd_text = "\n".join(cmds)
        self.assertIn("tc qdisc add dev eth0 root handle 1: htb default 30", cmd_text)
        self.assertIn("classid 1:10 htb rate 55.0mbit", cmd_text)
        self.assertIn("classid 1:20 htb rate 30.0mbit", cmd_text)
        self.assertIn("classid 1:30 htb rate 15.0mbit", cmd_text)
        self.assertIn("match ip dport 5060", cmd_text) # VoIP SIP filter

    def test_qos_engine_validation(self):
        """QoS engine must reject bandwidth allocations that do not equal 100%."""
        engine = QoSEngine()
        # Invalid percentage (sum = 90%)
        ok, msg = engine.update_policy(50.0, 30.0, 10.0, total_bw=100.0)
        self.assertFalse(ok)
        self.assertIn("Total percentage must sum to 100%", msg)

        # Valid percentage (sum = 100%)
        ok_valid, res = engine.update_policy(55.0, 30.0, 15.0, total_bw=100.0)
        self.assertTrue(ok_valid)

    def test_performance_evaluator_before_after_comparison(self):
        """Verify Scenario 1 vs Scenario 2 benchmark and CSV file generation."""
        evaluator = PerformanceEvaluator()
        report = evaluator.run_evaluation(test_name="Unit Test Benchmark", run_mode="SIMULATION")

        self.assertIn("test_id", report)
        self.assertIn("csv_filename", report)
        self.assertTrue(os.path.exists(report["csv_path"]))

        # Verify Scenario 1 has higher voice latency than Scenario 2
        before_voice = report["before_qos"][0]
        after_voice = report["after_qos"][0]
        self.assertGreater(before_voice["latency_ms"], after_voice["latency_ms"])
        self.assertEqual(after_voice["packet_loss_percent"], 0.0)

    def test_api_qos_and_performance(self):
        """Test QoS and Performance Flask API endpoints."""
        res_qos = self.client.get("/api/qos/policies")
        self.assertEqual(res_qos.status_code, 200)
        self.assertTrue(res_qos.get_json()["success"])

        res_perf = self.client.post("/api/performance/benchmark", json={"mode": "SIMULATION"})
        self.assertEqual(res_perf.status_code, 200)
        self.assertTrue(res_perf.get_json()["success"])

if __name__ == "__main__":
    unittest.main()
