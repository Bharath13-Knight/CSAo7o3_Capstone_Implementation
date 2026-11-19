import os
import sys
from pathlib import Path
from flask import Flask, render_template, jsonify, send_from_directory

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import Config
from database.database import init_db

# Ensure DB initialized before loading routes & services
init_db()

from backend.routes import (
    topology_bp,
    monitoring_bp,
    classification_bp,
    qos_bp,
    performance_bp,
    report_bp,
    settings_bp
)

def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder=str(PROJECT_ROOT / "frontend" / "templates"),
        static_folder=str(PROJECT_ROOT / "frontend" / "static")
    )
    app.config.from_object(config_class)

    # Initialize Database
    with app.app_context():
        init_db()

    # Register Blueprints
    app.register_blueprint(topology_bp)
    app.register_blueprint(monitoring_bp)
    app.register_blueprint(classification_bp)
    app.register_blueprint(qos_bp)
    app.register_blueprint(performance_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(settings_bp)

    # 1. Overview Dashboard Page
    @app.route("/")
    @app.route("/dashboard")
    def page_dashboard():
        return render_template("dashboard.html", active_page="dashboard")

    # 2. Network Topology Page
    @app.route("/topology")
    def page_topology():
        return render_template("topology.html", active_page="topology")

    # 3. Traffic Monitoring Page
    @app.route("/monitoring")
    def page_monitoring():
        return render_template("monitoring.html", active_page="monitoring")

    # 4. Traffic Classification Page
    @app.route("/classification")
    def page_classification():
        return render_template("classification.html", active_page="classification")

    # 5. QoS Management Page
    @app.route("/qos")
    def page_qos():
        return render_template("qos.html", active_page="qos")

    # 6. Performance Analysis Page
    @app.route("/performance")
    def page_performance():
        return render_template("performance.html", active_page="performance")

    # 7. Reports Page
    @app.route("/reports")
    def page_reports():
        return render_template("reports.html", active_page="reports")

    # 8. Settings Page
    @app.route("/settings")
    def page_settings():
        return render_template("settings.html", active_page="settings")

    # Error Handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template("base.html", error_title="404 - Page Not Found", error_msg="The requested network management page could not be located."), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"success": False, "error": "Internal Network Management Server Error"}), 500

    return app

if __name__ == "__main__":
    app = create_app()
    print("=" * 70)
    print(" Intelligent Multi-Subnet Network Traffic Management System")
    print(" Computer Networks Capstone Project")
    print(f" Web Interface: http://{Config.HOST}:{Config.PORT}/")
    print("=" * 70)
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
