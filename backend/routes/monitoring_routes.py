from flask import Blueprint, jsonify, request
from backend.services.monitoring_service import MonitoringService

monitoring_bp = Blueprint("monitoring_bp", __name__)
service = MonitoringService()

@monitoring_bp.route("/api/monitoring/status", methods=["GET"])
def get_status():
    status = service.get_status()
    return jsonify({"success": True, "status": status})

@monitoring_bp.route("/api/monitoring/start", methods=["POST"])
def start_monitoring():
    body = request.get_json() or {}
    mode = body.get("mode", "SIMULATION")
    interface = body.get("interface")
    rate = int(body.get("rate", 10))

    res = service.start_monitoring(mode=mode, interface=interface, rate=rate)
    return jsonify({"success": True, "result": res})

@monitoring_bp.route("/api/monitoring/stop", methods=["POST"])
def stop_monitoring():
    res = service.stop_monitoring()
    return jsonify({"success": True, "result": res})

@monitoring_bp.route("/api/monitoring/clear", methods=["POST"])
def clear_traffic():
    res = service.clear_traffic()
    return jsonify({"success": True, "result": res})

@monitoring_bp.route("/api/monitoring/packets", methods=["GET"])
def get_packets():
    limit = int(request.args.get("limit", 50))
    protocol = request.args.get("protocol", "ALL")
    priority = request.args.get("priority", "ALL")
    src_ip = request.args.get("src_ip", "")
    dst_ip = request.args.get("dst_ip", "")

    packets = service.get_packets(limit=limit, protocol=protocol, priority=priority, src_ip=src_ip, dst_ip=dst_ip)
    return jsonify({"success": True, "count": len(packets), "packets": packets})
