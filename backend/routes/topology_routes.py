from flask import Blueprint, jsonify, request
from backend.services.topology_service import TopologyService

topology_bp = Blueprint("topology_bp", __name__)
service = TopologyService()

@topology_bp.route("/api/topology", methods=["GET"])
def get_topology():
    data = service.get_topology()
    return jsonify({"success": True, "data": data})

@topology_bp.route("/api/topology/subnets", methods=["GET"])
def get_subnets():
    data = service.get_subnet_status()
    return jsonify({"success": True, "subnets": data})

@topology_bp.route("/api/topology/ping", methods=["POST"])
def ping_node():
    body = request.get_json() or {}
    source_ip = body.get("source_ip", "192.168.1.10")
    target_ip = body.get("target_ip", "192.168.2.10")
    count = int(body.get("count", 4))

    result = service.ping(source_ip, target_ip, count)
    return jsonify({"success": True, "result": result})

@topology_bp.route("/api/topology/device/toggle", methods=["POST"])
def toggle_device():
    body = request.get_json() or {}
    device_id = body.get("device_id")
    status = body.get("status", "ONLINE")
    if not device_id:
        return jsonify({"success": False, "error": "device_id is required"}), 400
    res = service.toggle_device(device_id, status)
    return jsonify({"success": True, "data": res})
