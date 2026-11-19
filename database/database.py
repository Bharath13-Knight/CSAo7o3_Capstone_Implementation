import sqlite3
import os
import logging
from config import Config

logger = logging.getLogger(__name__)

def get_db_connection():
    """Create and return a connection to the SQLite database with row factory."""
    db_path = Config.DATABASE_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    need_init = not os.path.exists(db_path)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    if need_init:
        _create_tables_and_seed(conn)
    return conn

def init_db():
    """Initialize database tables and seed default configuration if empty."""
    conn = sqlite3.connect(Config.DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _create_tables_and_seed(conn)
    conn.close()
    logger.info("Database initialized successfully at %s", Config.DATABASE_PATH)

def _create_tables_and_seed(conn):
    cursor = conn.cursor()

    # 1. Subnets Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subnets (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        cidr TEXT NOT NULL,
        gateway TEXT NOT NULL,
        vlan INTEGER DEFAULT 10,
        status TEXT DEFAULT 'UP',
        description TEXT
    );
    """)

    # 2. Devices Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS devices (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        ip TEXT NOT NULL UNIQUE,
        mac TEXT NOT NULL UNIQUE,
        subnet_id TEXT NOT NULL,
        type TEXT DEFAULT 'Workstation',
        status TEXT DEFAULT 'ONLINE',
        FOREIGN KEY (subnet_id) REFERENCES subnets(id)
    );
    """)

    # 3. Captured Packets Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS captured_packets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        src_ip TEXT NOT NULL,
        dst_ip TEXT NOT NULL,
        src_port INTEGER,
        dst_port INTEGER,
        protocol TEXT NOT NULL,
        length INTEGER NOT NULL,
        priority TEXT NOT NULL,
        application TEXT,
        info TEXT,
        mode TEXT DEFAULT 'SIMULATION'
    );
    """)

    # Index for fast querying on monitoring table
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_packets_time ON captured_packets(timestamp);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_packets_priority ON captured_packets(priority);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_packets_protocol ON captured_packets(protocol);")

    # 4. Traffic Classification Rules Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS traffic_classification_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        protocol TEXT NOT NULL,
        port_range TEXT,
        priority TEXT NOT NULL,
        app_name TEXT NOT NULL,
        description TEXT,
        is_active INTEGER DEFAULT 1
    );
    """)

    # 5. QoS Policies Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS qos_policies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        priority_level TEXT NOT NULL UNIQUE,
        allocated_bandwidth_mbps REAL NOT NULL,
        guaranteed_bandwidth_percent REAL NOT NULL,
        max_bandwidth_percent REAL NOT NULL,
        burst_rate_kb INTEGER DEFAULT 32,
        drop_policy TEXT DEFAULT 'TailDrop',
        status TEXT DEFAULT 'ENABLED'
    );
    """)

    # 6. Performance Measurements Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS performance_measurements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_id TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        scenario TEXT NOT NULL,
        traffic_type TEXT NOT NULL,
        throughput_mbps REAL NOT NULL,
        latency_ms REAL NOT NULL,
        packet_loss_percent REAL NOT NULL,
        jitter_ms REAL NOT NULL,
        bandwidth_util_percent REAL NOT NULL,
        test_duration_sec REAL DEFAULT 5.0,
        notes TEXT
    );
    """)

    # 7. Monitoring Sessions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS monitoring_sessions (
        session_id TEXT PRIMARY KEY,
        start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        end_time DATETIME,
        total_packets INTEGER DEFAULT 0,
        high_count INTEGER DEFAULT 0,
        med_count INTEGER DEFAULT 0,
        low_count INTEGER DEFAULT 0,
        mode TEXT DEFAULT 'SIMULATION'
    );
    """)

    # 8. Settings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    """)

    conn.commit()

    # Seed initial data if tables are empty
    _seed_initial_data(conn)
    logger.info("Database initialized successfully at %s", Config.DATABASE_PATH)

def _seed_initial_data(conn):
    cursor = conn.cursor()

    # Seed Subnets
    cursor.execute("SELECT COUNT(*) FROM subnets;")
    if cursor.fetchone()[0] == 0:
        for s in Config.DEFAULT_SUBNETS:
            cursor.execute("""
                INSERT INTO subnets (id, name, cidr, gateway, vlan, status, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (s["id"], s["name"], s["cidr"], s["gateway"], s["vlan"], s["status"], s["description"]))

    # Seed Devices
    cursor.execute("SELECT COUNT(*) FROM devices;")
    if cursor.fetchone()[0] == 0:
        for d in Config.DEFAULT_DEVICES:
            cursor.execute("""
                INSERT INTO devices (id, name, ip, mac, subnet_id, type, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (d["id"], d["name"], d["ip"], d["mac"], d["subnet_id"], d["type"], d["status"]))

    # Seed Classification Rules
    cursor.execute("SELECT COUNT(*) FROM traffic_classification_rules;")
    if cursor.fetchone()[0] == 0:
        default_rules = [
            # High Priority: Voice, Video, Real-Time
            ("VoIP SIP Signaling", "UDP", "5060,5061", "HIGH", "VoIP (SIP)", "Session Initiation Protocol signaling"),
            ("RTP Real-time Audio", "UDP", "10000-20000", "HIGH", "VoIP (RTP)", "Real-time voice stream packets"),
            ("Zoom / Teams Conferencing", "UDP", "8801-8802,3478", "HIGH", "Video Conference", "Real-time video conferencing media streams"),
            ("ICMP Ping Diagnostics", "ICMP", "0", "HIGH", "Network Diagnostics", "Latency-sensitive ping probes"),
            
            # Medium Priority: Web, DNS, Standard Business
            ("DNS Lookups", "UDP", "53", "MEDIUM", "DNS", "Domain Name System queries"),
            ("HTTP Web Browsing", "TCP", "80", "MEDIUM", "HTTP Web", "Standard unencrypted web browsing traffic"),
            ("HTTPS Secure Web", "TCP", "443", "MEDIUM", "HTTPS Web", "TLS encrypted web and API traffic"),
            ("SSH Remote Shell", "TCP", "22", "MEDIUM", "SSH Terminal", "Interactive administrative console session"),
            
            # Low Priority: Bulk Downloads, File Transfers, Backups
            ("FTP Control and Data", "TCP", "20,21", "LOW", "FTP Bulk Transfer", "Large bulk file transfer protocol"),
            ("BitTorrent P2P", "TCP", "6881-6889", "LOW", "P2P BitTorrent", "Peer-to-peer file distribution traffic"),
            ("Database Backup Sync", "TCP", "3306,5432,873", "LOW", "Server Backup", "Bulk automated database replica and sync"),
            ("Background HTTP Downloads", "TCP", "8080,8000", "LOW", "Bulk Downloads", "Non-interactive bulk file downloads")
        ]
        for name, proto, port, prio, app, desc in default_rules:
            cursor.execute("""
                INSERT INTO traffic_classification_rules (name, protocol, port_range, priority, app_name, description, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (name, proto, port, prio, app, desc))

    # Seed QoS Policies
    cursor.execute("SELECT COUNT(*) FROM qos_policies;")
    if cursor.fetchone()[0] == 0:
        default_policies = [
            ("Voice & Video Real-time Guarantee", "HIGH", 55.0, 55.0, 95.0, 64, "StrictPriority", "ENABLED"),
            ("Interactive Web & Business Applications", "MEDIUM", 30.0, 30.0, 80.0, 32, "FairQueuing", "ENABLED"),
            ("Bulk Downloads & File Transfers", "LOW", 15.0, 15.0, 40.0, 16, "RateLimitedTailDrop", "ENABLED")
        ]
        for name, prio, bw, guar, max_bw, burst, drop_p, status in default_policies:
            cursor.execute("""
                INSERT INTO qos_policies (name, priority_level, allocated_bandwidth_mbps, guaranteed_bandwidth_percent, max_bandwidth_percent, burst_rate_kb, drop_policy, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, prio, bw, guar, max_bw, burst, drop_p, status))

    # Seed Default Settings
    cursor.execute("SELECT COUNT(*) FROM settings;")
    if cursor.fetchone()[0] == 0:
        default_settings = [
            ("monitoring_mode", Config.DEFAULT_MONITORING_MODE),
            ("qos_enabled", "1"),
            ("total_bandwidth_mbps", str(Config.TOTAL_BANDWIDTH_MBPS)),
            ("capture_interface", Config.DEFAULT_INTERFACE),
            ("packet_generation_rate", str(Config.MONITORING_RATE_PACKETS_PER_SEC)),
            ("system_status", "OPERATIONAL")
        ]
        for k, v in default_settings:
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (k, v))

    conn.commit()
