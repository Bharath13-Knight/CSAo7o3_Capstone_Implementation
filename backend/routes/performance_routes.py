from flask import Blueprint, jsonify, request
from backend.services.performance_service import PerformanceService

performance_bp = Blueprint("performance_bp", __name__)
service = PerformanceService()

@performance_bp.route("/api/performance/benchmark", methods=["POST"])
def run_benchmark():
    body = request.get_json() or {}
    mode = body.get("mode", "SIMULATION")
    data = service.run_benchmark(mode=mode)
    return jsonify({"success": True, "benchmark": data})

@performance_bp.route("/api/performance/latest", methods=["GET"])
def get_latest():
    data = service.get_latest_comparison()
    return jsonify({"success": True, "data": data})

@performance_bp.route("/api/performance/history", methods=["GET"])
def get_history():
    limit = int(request.args.get("limit", 30))
    history = service.get_history(limit=limit)
    return jsonify({"success": True, "history": history})
