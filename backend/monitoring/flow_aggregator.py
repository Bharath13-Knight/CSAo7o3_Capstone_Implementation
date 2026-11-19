import time
from collections import deque
import threading
from config import Config
from database.models import PacketModel

class FlowAggregator:
    """
    Maintains real-time packet statistics, bandwidth telemetry,
    and rolling history buffers for Chart.js streaming graphs.
    """

    def __init__(self, history_size=60):
        self.history_size = history_size
        self._lock = threading.Lock()
        
        # Time-series history buffers (per-second buckets)
        self.time_labels = deque(maxlen=history_size)
        self.bandwidth_in_history = deque(maxlen=history_size)   # Mbps
        self.bandwidth_out_history = deque(maxlen=history_size)  # Mbps
        self.high_prio_rate_history = deque(maxlen=history_size) # pps
        self.med_prio_rate_history = deque(maxlen=history_size)  # pps
        self.low_prio_rate_history = deque(maxlen=history_size)  # pps

        # Sliding window for current second
        self.current_window_start = time.time()
        self.window_bytes_in = 0
        self.window_bytes_out = 0
        self.window_high_packets = 0
        self.window_med_packets = 0
        self.window_low_packets = 0

        # Memory buffer for recent captured packets
        self.recent_packets_buffer = deque(maxlen=Config.MAX_PACKETS_IN_MEMORY)

        # Totals
        self.total_packets_count = 0
        self.total_bytes_count = 0
        self.priority_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        self.protocol_counts = {"TCP": 0, "UDP": 0, "ICMP": 0, "DNS": 0, "HTTP": 0, "OTHER": 0}

        # Initialize rolling buffer with zero baselines
        now = time.strftime("%H:%M:%S")
        for _ in range(20):
            self.time_labels.append(now)
            self.bandwidth_in_history.append(0.0)
            self.bandwidth_out_history.append(0.0)
            self.high_prio_rate_history.append(0)
            self.med_prio_rate_history.append(0)
            self.low_prio_rate_history.append(0)

    def record_packet(self, packet_dict):
        """Record a single incoming/outgoing packet."""
        with self._lock:
            self.recent_packets_buffer.appendleft(packet_dict)
            self.total_packets_count += 1
            length = packet_dict.get("length", 64)
            self.total_bytes_count += length

            prio = packet_dict.get("priority", "MEDIUM")
            self.priority_counts[prio] = self.priority_counts.get(prio, 0) + 1

            proto = packet_dict.get("protocol", "OTHER")
            self.protocol_counts[proto] = self.protocol_counts.get(proto, 0) + 1

            # Determine incoming vs outgoing relative to Subnets
            # Traffic destined for Subnet A, B, or C is incoming; originating from them is outgoing
            dst_ip = packet_dict.get("dst_ip", "")
            src_ip = packet_dict.get("src_ip", "")
            if dst_ip.startswith("192.168."):
                self.window_bytes_in += length
            else:
                self.window_bytes_out += length

            if prio == "HIGH":
                self.window_high_packets += 1
            elif prio == "LOW":
                self.window_low_packets += 1
            else:
                self.window_med_packets += 1

            self._check_and_flush_window()

    def _check_and_flush_window(self):
        """Check if 1 second has elapsed; if so, push rates to rolling histories."""
        now = time.time()
        elapsed = now - self.current_window_start
        if elapsed >= 1.0:
            # Convert bytes in 1 second to Megabits per second (Mbps)
            bw_in_mbps = round((self.window_bytes_in * 8) / (elapsed * 1_000_000), 3)
            bw_out_mbps = round((self.window_bytes_out * 8) / (elapsed * 1_000_000), 3)

            ts_str = time.strftime("%H:%M:%S")
            self.time_labels.append(ts_str)
            self.bandwidth_in_history.append(bw_in_mbps)
            self.bandwidth_out_history.append(bw_out_mbps)
            self.high_prio_rate_history.append(self.window_high_packets)
            self.med_prio_rate_history.append(self.window_med_packets)
            self.low_prio_rate_history.append(self.window_low_packets)

            # Reset window
            self.current_window_start = now
            self.window_bytes_in = 0
            self.window_bytes_out = 0
            self.window_high_packets = 0
            self.window_med_packets = 0
            self.window_low_packets = 0

    def get_live_metrics(self):
        """Returns consolidated live metrics for dashboard and monitoring page."""
        with self._lock:
            self._check_and_flush_window()
            
            cur_bw_in = self.bandwidth_in_history[-1] if self.bandwidth_in_history else 0.0
            cur_bw_out = self.bandwidth_out_history[-1] if self.bandwidth_out_history else 0.0
            total_bw = round(cur_bw_in + cur_bw_out, 3)
            
            utilization_pct = round(min(100.0, (total_bw / Config.TOTAL_BANDWIDTH_MBPS) * 100), 1)
            
            total_p = max(1, self.total_packets_count)
            high_pct = round((self.priority_counts.get("HIGH", 0) / total_p) * 100, 1)

            return {
                "total_packets": self.total_packets_count,
                "total_bytes": self.total_bytes_count,
                "bandwidth_in_mbps": cur_bw_in,
                "bandwidth_out_mbps": cur_bw_out,
                "total_bandwidth_mbps": total_bw,
                "bandwidth_utilization_pct": utilization_pct,
                "high_priority_pct": high_pct,
                "priority_counts": dict(self.priority_counts),
                "protocol_counts": dict(self.protocol_counts),
                "time_series": {
                    "labels": list(self.time_labels),
                    "bandwidth_in": list(self.bandwidth_in_history),
                    "bandwidth_out": list(self.bandwidth_out_history),
                    "high_rate": list(self.high_prio_rate_history),
                    "med_rate": list(self.med_prio_rate_history),
                    "low_rate": list(self.low_prio_rate_history)
                }
            }

    def get_recent_packets(self, limit=50, protocol="ALL", priority="ALL", src_ip="", dst_ip=""):
        """Filter recent packets from in-memory ring buffer."""
        with self._lock:
            result = []
            for p in self.recent_packets_buffer:
                if protocol != "ALL" and p.get("protocol") != protocol:
                    continue
                if priority != "ALL" and p.get("priority") != priority:
                    continue
                if src_ip and src_ip not in p.get("src_ip", ""):
                    continue
                if dst_ip and dst_ip not in p.get("dst_ip", ""):
                    continue
                result.append(p)
                if len(result) >= limit:
                    break
            return result

    def clear(self):
        """Clear all metrics and ring buffers."""
        with self._lock:
            self.recent_packets_buffer.clear()
            self.total_packets_count = 0
            self.total_bytes_count = 0
            self.priority_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
            self.protocol_counts = {"TCP": 0, "UDP": 0, "ICMP": 0, "DNS": 0, "HTTP": 0, "OTHER": 0}
            self.window_bytes_in = 0
            self.window_bytes_out = 0
            self.window_high_packets = 0
            self.window_med_packets = 0
            self.window_low_packets = 0
