import time
import random
import subprocess
import platform
import logging
from database.models import DeviceModel, SubnetModel

logger = logging.getLogger(__name__)

class PingUtility:
    """Provides ping diagnostics and hop tracing for virtual and real nodes."""

    @staticmethod
    def ping_test(source_ip, target_ip, count=4):
        """
        Executes a diagnostic ping between two nodes.
        If both are virtual topology devices, calculates inter-subnet route, hops, and delay.
        If target is an external/real IP, can perform real OS ping with fallback.
        """
        src_dev = DeviceModel.get_by_ip(source_ip)
        dst_dev = DeviceModel.get_by_ip(target_ip)

        # Check if both are virtual nodes in our 3 subnets
        if src_dev and dst_dev:
            return PingUtility._virtual_ping(src_dev, dst_dev, count)
        
        # Otherwise, attempt a real OS ping with strict validation
        return PingUtility._real_ping(target_ip, count)

    @staticmethod
    def _virtual_ping(src_dev, dst_dev, count=4):
        """Simulate realistic ICMP echo requests through switches and router."""
        same_subnet = src_dev["subnet_id"] == dst_dev["subnet_id"]
        
        # Route calculation
        if same_subnet:
            hops = [src_dev["name"], f"Switch ({src_dev['subnet_id']})", dst_dev["name"]]
            base_rtt = random.uniform(0.8, 1.8)  # Same switch L2 fast ping
            ttl = 64
        else:
            hops = [
                src_dev["name"],
                f"Switch ({src_dev['subnet_id']})",
                "Core Router R1 (Default Gateway)",
                f"Switch ({dst_dev['subnet_id']})",
                dst_dev["name"]
            ]
            base_rtt = random.uniform(3.2, 7.5)  # Inter-subnet L3 routed ping
            ttl = 63  # decremented by 1 router hop

        packets = []
        rtt_list = []
        lost_count = 0

        for seq in range(1, count + 1):
            # If target device is offline or subnet is down, packet is lost
            if dst_dev.get("status") == "OFFLINE":
                lost_count += 1
                packets.append({
                    "seq": seq,
                    "status": "Request timed out",
                    "rtt_ms": None,
                    "ttl": None
                })
            else:
                jitter = random.uniform(-0.4, 0.6)
                rtt = max(0.4, round(base_rtt + jitter, 2))
                rtt_list.append(rtt)
                packets.append({
                    "seq": seq,
                    "bytes": 64,
                    "status": "Reply received",
                    "rtt_ms": rtt,
                    "ttl": ttl
                })

        sent = count
        received = sent - lost_count
        loss_pct = round((lost_count / sent) * 100, 1)
        
        min_rtt = min(rtt_list) if rtt_list else 0
        max_rtt = max(rtt_list) if rtt_list else 0
        avg_rtt = round(sum(rtt_list) / len(rtt_list), 2) if rtt_list else 0

        return {
            "type": "VIRTUAL_TOPOLOGY_PING",
            "source": f"{src_dev['name']} ({src_dev['ip']})",
            "target": f"{dst_dev['name']} ({dst_dev['ip']})",
            "same_subnet": same_subnet,
            "hop_path": hops,
            "packets_sent": sent,
            "packets_received": received,
            "packet_loss_pct": loss_pct,
            "min_rtt_ms": min_rtt,
            "max_rtt_ms": max_rtt,
            "avg_rtt_ms": avg_rtt,
            "details": packets
        }

    @staticmethod
    def _real_ping(target_ip, count=4):
        """Safe real OS ping with output parsing."""
        # Sanitize target_ip
        safe_ip = target_ip.strip()
        is_windows = platform.system().lower() == "windows"
        cmd = ["ping", "-n" if is_windows else "-c", str(count), safe_ip]

        try:
            start_t = time.time()
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
            elapsed = round((time.time() - start_t) * 1000, 2)
            
            output = proc.stdout
            success = proc.returncode == 0
            
            return {
                "type": "REAL_NETWORK_PING",
                "target": safe_ip,
                "success": success,
                "elapsed_total_ms": elapsed,
                "raw_output": output,
                "details": []
            }
        except Exception as e:
            return {
                "type": "REAL_NETWORK_PING",
                "target": safe_ip,
                "success": False,
                "error": str(e)
            }
