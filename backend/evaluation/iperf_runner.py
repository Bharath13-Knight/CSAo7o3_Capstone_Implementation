import shutil
import subprocess
import socket
import time
import logging

logger = logging.getLogger(__name__)

class IperfRunner:
    """
    Handles performance benchmarking using iperf3 if installed,
    or a native Python TCP socket loopback benchmark.
    """

    @staticmethod
    def is_iperf3_available():
        """Check if iperf3 CLI utility is installed on the host."""
        return shutil.which("iperf3") is not None

    @staticmethod
    def run_socket_benchmark(duration_sec=3.0, port=5201):
        """
        Runs a quick native socket loopback benchmark measuring actual
        local TCP throughput and ping latency on the host.
        """
        try:
            # Measure local loopback ping
            start_ping = time.perf_counter()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.0)
            # Test connect to local port (or self bind)
            s.bind(('127.0.0.1', 0))
            bound_port = s.getsockname()[1]
            s.listen(1)
            
            # Connect from client socket
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('127.0.0.1', bound_port))
            server_conn, _ = s.accept()
            ping_ms = round((time.perf_counter() - start_ping) * 1000, 2)

            # Throughput measurement: blast 64KB blocks for duration_sec
            test_data = b"X" * 65536
            total_bytes = 0
            start_blast = time.perf_counter()
            end_time = start_blast + duration_sec

            while time.perf_counter() < end_time:
                client.sendall(test_data)
                received = server_conn.recv(65536)
                total_bytes += len(received)

            elapsed = time.perf_counter() - start_blast
            client.close()
            server_conn.close()
            s.close()

            throughput_mbps = round((total_bytes * 8) / (elapsed * 1_000_000), 2)
            return {
                "success": True,
                "mode": "REAL_SOCKET_LOOPBACK",
                "throughput_mbps": throughput_mbps,
                "latency_ms": max(0.2, ping_ms),
                "duration_sec": round(elapsed, 2),
                "total_mb_transferred": round(total_bytes / (1024 * 1024), 2)
            }
        except Exception as e:
            logger.warning("Socket benchmark failed: %s", e)
            return {
                "success": False,
                "mode": "REAL_SOCKET_LOOPBACK",
                "error": str(e)
            }
