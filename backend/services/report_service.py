import os
import glob
from config import Config
from database.models import PerformanceModel, PacketModel

class ReportService:
    def __init__(self):
        self.reports_dir = Config.REPORTS_DIR
        os.makedirs(self.reports_dir, exist_ok=True)

    def list_reports(self):
        """List all generated CSV and benchmark reports."""
        files = glob.glob(os.path.join(self.reports_dir, "*.csv"))
        reports = []
        for f in files:
            stat = os.stat(f)
            reports.append({
                "filename": os.path.basename(f),
                "path": f,
                "size_kb": round(stat.st_size / 1024, 2),
                "created_at": os.path.getmtime(f)
            })
        reports.sort(key=lambda x: x["created_at"], reverse=True)
        return reports

    def get_summary_statistics(self):
        """Returns consolidated performance and traffic statistics for reporting."""
        packet_counts = PacketModel.get_counts()
        recent_tests = PerformanceModel.get_recent(limit=10)
        latest_comparison = PerformanceModel.get_latest_comparison()
        
        return {
            "traffic": packet_counts,
            "recent_tests": recent_tests,
            "latest_comparison": latest_comparison
        }
