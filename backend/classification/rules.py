"""
Traffic Classification Rules & Port Mappings
Classifies traffic into:
- HIGH: Voice (VoIP/SIP/RTP), Video Conferencing, Real-time audio/video, Delay-sensitive probes
- MEDIUM: Web (HTTP, HTTPS), DNS queries, Standard interactive apps (SSH)
- LOW: Large file transfers (FTP/SFTP), BitTorrent/P2P, Background downloads, Server backups
"""

DEFAULT_PORT_CLASSIFICATIONS = {
    # High Priority: Voice & Video Real-Time
    5060: {"app": "VoIP (SIP)", "priority": "HIGH", "category": "Voice"},
    5061: {"app": "VoIP (SIP-TLS)", "priority": "HIGH", "category": "Voice"},
    5004: {"app": "RTP Audio", "priority": "HIGH", "category": "Voice"},
    5005: {"app": "RTCP Control", "priority": "HIGH", "category": "Voice"},
    3478: {"app": "STUN/TURN (WebRTC)", "priority": "HIGH", "category": "Real-time Media"},
    8801: {"app": "Zoom Video", "priority": "HIGH", "category": "Video Conference"},
    8802: {"app": "Zoom Audio/Screen", "priority": "HIGH", "category": "Video Conference"},
    1935: {"app": "RTMP Live Stream", "priority": "HIGH", "category": "Live Streaming"},

    # Medium Priority: Web & Interactive
    53:   {"app": "DNS Query", "priority": "MEDIUM", "category": "Name Resolution"},
    80:   {"app": "HTTP Web", "priority": "MEDIUM", "category": "Web Browsing"},
    443:  {"app": "HTTPS Secure Web", "priority": "MEDIUM", "category": "Secure Web / API"},
    22:   {"app": "SSH Console", "priority": "MEDIUM", "category": "Remote Admin"},
    8080: {"app": "HTTP Alternate", "priority": "MEDIUM", "category": "Web App"},

    # Low Priority: Bulk & Background Data Transfers
    20:   {"app": "FTP Data", "priority": "LOW", "category": "File Transfer"},
    21:   {"app": "FTP Control", "priority": "LOW", "category": "File Transfer"},
    25:   {"app": "SMTP Mail", "priority": "LOW", "category": "Bulk Mail"},
    6881: {"app": "BitTorrent P2P", "priority": "LOW", "category": "P2P"},
    6882: {"app": "BitTorrent P2P", "priority": "LOW", "category": "P2P"},
    3306: {"app": "MySQL Sync", "priority": "LOW", "category": "Database Sync"},
    5432: {"app": "PostgreSQL Replica", "priority": "LOW", "category": "Database Sync"},
    873:  {"app": "Rsync Backup", "priority": "LOW", "category": "Bulk Backup"}
}
