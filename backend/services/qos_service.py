from backend.qos.qos_engine import QoSEngine

class QoSService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(QoSService, cls).__new__(cls)
            cls._instance.engine = QoSEngine()
        return cls._instance

    def get_policies(self):
        return self.engine.get_policies()

    def update_policies(self, high_pct, med_pct, low_pct, total_bw=None):
        return self.engine.update_policy(high_pct, med_pct, low_pct, total_bw)

    def toggle_qos(self, enabled=True):
        return self.engine.toggle_qos(enabled)

    def get_tc_script(self):
        return self.engine.get_generated_tc_commands()
