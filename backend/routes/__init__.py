from backend.routes.topology_routes import topology_bp
from backend.routes.monitoring_routes import monitoring_bp
from backend.routes.classification_routes import classification_bp
from backend.routes.qos_routes import qos_bp
from backend.routes.performance_routes import performance_bp
from backend.routes.report_routes import report_bp
from backend.routes.settings_routes import settings_bp

__all__ = [
    "topology_bp",
    "monitoring_bp",
    "classification_bp",
    "qos_bp",
    "performance_bp",
    "report_bp",
    "settings_bp"
]
