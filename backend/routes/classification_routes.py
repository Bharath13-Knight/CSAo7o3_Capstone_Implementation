from flask import Blueprint, jsonify, request
from backend.services.classification_service import ClassificationService

classification_bp = Blueprint("classification_bp", __name__)
service = ClassificationService()

@classification_bp.route("/api/classification/rules", methods=["GET"])
def get_rules():
    rules = service.get_rules()
    return jsonify({"success": True, "rules": rules})

@classification_bp.route("/api/classification/rules", methods=["POST"])
def add_rule():
    body = request.get_json() or {}
    name = body.get("name")
    protocol = body.get("protocol", "TCP")
    port_range = body.get("port_range", "")
    priority = body.get("priority", "MEDIUM")
    app_name = body.get("app_name", name)
    description = body.get("description", "")

    if not name:
        return jsonify({"success": False, "error": "Rule name is required"}), 400

    new_rule = service.add_rule(name, protocol, port_range, priority, app_name, description)
    return jsonify({"success": True, "rule": new_rule})

@classification_bp.route("/api/classification/rules/<int:rule_id>", methods=["DELETE"])
def delete_rule(rule_id):
    res = service.delete_rule(rule_id)
    return jsonify({"success": True, "result": res})

@classification_bp.route("/api/classification/rules/<int:rule_id>/toggle", methods=["POST"])
def toggle_rule(rule_id):
    body = request.get_json() or {}
    is_active = int(body.get("is_active", 1))
    res = service.toggle_rule(rule_id, is_active)
    return jsonify({"success": True, "result": res})

@classification_bp.route("/api/classification/stats", methods=["GET"])
def get_stats():
    stats = service.get_stats()
    return jsonify({"success": True, "stats": stats})
