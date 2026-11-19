from flask import Blueprint, jsonify, request
from database.models import SettingsModel
from database.database import init_db

settings_bp = Blueprint("settings_bp", __name__)

@settings_bp.route("/api/settings", methods=["GET"])
def get_settings():
    settings = SettingsModel.get_all()
    return jsonify({"success": True, "settings": settings})

@settings_bp.route("/api/settings", methods=["POST"])
def update_settings():
    body = request.get_json() or {}
    for k, v in body.items():
        SettingsModel.set(k, v)
    return jsonify({"success": True, "settings": SettingsModel.get_all()})

@settings_bp.route("/api/settings/reset", methods=["POST"])
def reset_settings():
    init_db()
    return jsonify({"success": True, "message": "Database and system configurations reset to default."})
