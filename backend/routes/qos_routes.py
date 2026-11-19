from flask import Blueprint, jsonify, request
from backend.services.qos_service import QoSService

qos_bp = Blueprint("qos_bp", __name__)
service = QoSService()

@qos_bp.route("/api/qos/policies", methods=["GET"])
def get_policies():
    data = service.get_policies()
    return jsonify({"success": True, "data": data})

@qos_bp.route("/api/qos/policies", methods=["POST"])
def update_policies():
    body = request.get_json() or {}
    try:
        high = float(body.get("high_pct", 55.0))
        med = float(body.get("med_pct", 30.0))
        low = float(body.get("low_pct", 15.0))
        total_bw = float(body.get("total_bandwidth_mbps", 100.0))
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Invalid numerical parameters"}), 400

    ok, res = service.update_policies(high, med, low, total_bw)
    if not ok:
        return jsonify({"success": False, "error": res}), 400
    return jsonify({"success": True, "result": res})

@qos_bp.route("/api/qos/toggle", methods=["POST"])
def toggle_qos():
    body = request.get_json() or {}
    enable = bool(body.get("enable", True))
    res = service.toggle_qos(enable)
    return jsonify({"success": True, "result": res})

@qos_bp.route("/api/qos/tc-script", methods=["GET"])
def get_tc_script():
    commands = service.get_tc_script()
    return jsonify({"success": True, "commands": commands})
