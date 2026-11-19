from backend.evaluation.evaluator import PerformanceEvaluator
from backend.services.qos_service import QoSService
from database.models import PerformanceModel

class PerformanceService:
    def __init__(self):
        qos_srv = QoSService()
        self.evaluator = PerformanceEvaluator(qos_engine=qos_srv.engine)

    def run_benchmark(self, mode="SIMULATION"):
        return self.evaluator.run_evaluation(run_mode=mode)

    def get_latest_comparison(self):
        return PerformanceModel.get_latest_comparison()

    def get_history(self, limit=30):
        return PerformanceModel.get_recent(limit=limit)
