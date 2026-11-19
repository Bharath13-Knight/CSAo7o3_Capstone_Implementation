from backend.classification.classifier import TrafficClassifier
from database.models import ClassificationRuleModel, PacketModel

class ClassificationService:
    def __init__(self):
        self.classifier = TrafficClassifier()

    def get_rules(self):
        return ClassificationRuleModel.get_all()

    def add_rule(self, name, protocol, port_range, priority, app_name, description=""):
        rule_id = ClassificationRuleModel.insert(name, protocol, port_range, priority, app_name, description)
        self.classifier.reload_rules()
        return {"id": rule_id, "name": name, "priority": priority}

    def delete_rule(self, rule_id):
        ClassificationRuleModel.delete(rule_id)
        self.classifier.reload_rules()
        return {"deleted": rule_id}

    def toggle_rule(self, rule_id, is_active):
        ClassificationRuleModel.toggle_active(rule_id, is_active)
        self.classifier.reload_rules()
        return {"id": rule_id, "is_active": is_active}

    def get_stats(self):
        counts = PacketModel.get_counts()
        total = max(1, counts["total_packets"])
        return {
            "total_packets": counts["total_packets"],
            "high_priority_count": counts["high_priority"],
            "medium_priority_count": counts["medium_priority"],
            "low_priority_count": counts["low_priority"],
            "high_priority_pct": round((counts["high_priority"] / total) * 100, 1),
            "medium_priority_pct": round((counts["medium_priority"] / total) * 100, 1),
            "low_priority_pct": round((counts["low_priority"] / total) * 100, 1),
            "protocols": counts["protocols"]
        }
