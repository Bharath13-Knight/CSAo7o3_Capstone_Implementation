from flask import Blueprint, jsonify, send_from_directory, abort
import os
from config import Config
from backend.services.report_service import ReportService

report_bp = Blueprint("report_bp", __name__)
service = ReportService()

@report_bp.route("/api/reports", methods=["GET"])
def list_reports():
    reports = service.list_reports()
    return jsonify({"success": True, "reports": reports})

@report_bp.route("/api/reports/download/<path:filename>", methods=["GET"])
def download_report(filename):
    # Sanitize filename
    safe_name = os.path.basename(filename)
    if not safe_name.endswith(".csv"):
        abort(400)
    file_path = os.path.join(Config.REPORTS_DIR, safe_name)
    if not os.path.exists(file_path):
        abort(404)
    return send_from_directory(Config.REPORTS_DIR, safe_name, as_attachment=True)

@report_bp.route("/api/reports/summary", methods=["GET"])
def get_summary():
    data = service.get_summary_statistics()
    return jsonify({"success": True, "summary": data})
