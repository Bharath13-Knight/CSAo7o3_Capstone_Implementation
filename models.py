import datetime
from database.database import get_db_connection

class SubnetModel:
    @staticmethod
    def get_all():
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM subnets ORDER BY id").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(subnet_id):
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM subnets WHERE id = ?", (subnet_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def update_status(subnet_id, status):
        conn = get_db_connection()
        conn.execute("UPDATE subnets SET status = ? WHERE id = ?", (status, subnet_id))
        conn.commit()
        conn.close()

class DeviceModel:
    @staticmethod
    def get_all():
        conn = get_db_connection()
        rows = conn.execute("""
            SELECT d.*, s.name as subnet_name, s.cidr as subnet_cidr 
            FROM devices d
            LEFT JOIN subnets s ON d.subnet_id = s.id
            ORDER BY d.ip
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_ip(ip):
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM devices WHERE ip = ?", (ip,)).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_by_subnet(subnet_id):
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM devices WHERE subnet_id = ?", (subnet_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

class PacketModel:
    @staticmethod
    def insert(session_id, src_ip, dst_ip, src_port, dst_port, protocol, length, priority, application, info, mode="SIMULATION"):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO captured_packets 
            (session_id, src_ip, dst_ip, src_port, dst_port, protocol, length, priority, application, info, mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (session_id, src_ip, dst_ip, src_port, dst_port, protocol, length, priority, application, info, mode))
        conn.commit()
        packet_id = cursor.lastrowid
        conn.close()
        return packet_id

    @staticmethod
    def get_recent(limit=50, protocol=None, priority=None, src_ip=None, dst_ip=None):
        conn = get_db_connection()
        query = "SELECT * FROM captured_packets WHERE 1=1"
        params = []
        if protocol and protocol != "ALL":
            query += " AND protocol = ?"
            params.append(protocol)
        if priority and priority != "ALL":
            query += " AND priority = ?"
            params.append(priority)
        if src_ip:
            query += " AND src_ip LIKE ?"
            params.append(f"%{src_ip}%")
        if dst_ip:
            query += " AND dst_ip LIKE ?"
            params.append(f"%{dst_ip}%")

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_counts():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM captured_packets")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT priority, COUNT(*) FROM captured_packets GROUP BY priority")
        prio_counts = {r[0]: r[1] for r in cursor.fetchall()}
        
        cursor.execute("SELECT protocol, COUNT(*) FROM captured_packets GROUP BY protocol")
        proto_counts = {r[0]: r[1] for r in cursor.fetchall()}

        cursor.execute("SELECT SUM(length) FROM captured_packets")
        sum_bytes = cursor.fetchone()[0] or 0

        conn.close()
        return {
            "total_packets": total,
            "total_bytes": sum_bytes,
            "high_priority": prio_counts.get("HIGH", 0),
            "medium_priority": prio_counts.get("MEDIUM", 0),
            "low_priority": prio_counts.get("LOW", 0),
            "protocols": proto_counts
        }

    @staticmethod
    def clear_all():
        conn = get_db_connection()
        conn.execute("DELETE FROM captured_packets")
        conn.commit()
        conn.close()

class ClassificationRuleModel:
    @staticmethod
    def get_all():
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM traffic_classification_rules ORDER BY id").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def insert(name, protocol, port_range, priority, app_name, description=""):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO traffic_classification_rules (name, protocol, port_range, priority, app_name, description, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (name, protocol, port_range, priority, app_name, description))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return new_id

    @staticmethod
    def delete(rule_id):
        conn = get_db_connection()
        conn.execute("DELETE FROM traffic_classification_rules WHERE id = ?", (rule_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def toggle_active(rule_id, is_active):
        conn = get_db_connection()
        conn.execute("UPDATE traffic_classification_rules SET is_active = ? WHERE id = ?", (is_active, rule_id))
        conn.commit()
        conn.close()

class QoSPolicyModel:
    @staticmethod
    def get_all():
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM qos_policies ORDER BY id").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def update(priority_level, allocated_bw, guaranteed_pct, max_pct, status="ENABLED"):
        conn = get_db_connection()
        conn.execute("""
            UPDATE qos_policies 
            SET allocated_bandwidth_mbps = ?, 
                guaranteed_bandwidth_percent = ?, 
                max_bandwidth_percent = ?,
                status = ?
            WHERE priority_level = ?
        """, (allocated_bw, guaranteed_pct, max_pct, status, priority_level))
        conn.commit()
        conn.close()

class PerformanceModel:
    @staticmethod
    def insert(test_id, scenario, traffic_type, throughput_mbps, latency_ms, packet_loss_percent, jitter_ms, bandwidth_util_percent, duration_sec=5.0, notes=""):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO performance_measurements
            (test_id, scenario, traffic_type, throughput_mbps, latency_ms, packet_loss_percent, jitter_ms, bandwidth_util_percent, test_duration_sec, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (test_id, scenario, traffic_type, throughput_mbps, latency_ms, packet_loss_percent, jitter_ms, bandwidth_util_percent, duration_sec, notes))
        conn.commit()
        row_id = cursor.lastrowid
        conn.close()
        return row_id

    @staticmethod
    def get_recent(limit=30):
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM performance_measurements ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_latest_comparison():
        conn = get_db_connection()
        before = conn.execute("SELECT * FROM performance_measurements WHERE scenario = 'BEFORE_QOS' ORDER BY id DESC LIMIT 1").fetchone()
        after = conn.execute("SELECT * FROM performance_measurements WHERE scenario = 'AFTER_QOS' ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()
        return {
            "before": dict(before) if before else None,
            "after": dict(after) if after else None
        }

class SettingsModel:
    @staticmethod
    def get(key, default=None):
        conn = get_db_connection()
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        conn.close()
        return row["value"] if row else default

    @staticmethod
    def set(key, value):
        conn = get_db_connection()
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
        conn.commit()
        conn.close()

    @staticmethod
    def get_all():
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM settings").fetchall()
        conn.close()
        return {r["key"]: r["value"] for r in rows}
