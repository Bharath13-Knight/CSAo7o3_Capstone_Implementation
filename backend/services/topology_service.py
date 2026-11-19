from backend.network.topology_manager import TopologyManager
from backend.network.ping_utility import PingUtility
from database.models import SubnetModel, DeviceModel

class TopologyService:
    def __init__(self):
        self.manager = TopologyManager()

    def get_topology(self):
        return self.manager.get_topology_data()

    def get_subnet_status(self):
        return self.manager.get_subnet_status()

    def ping(self, source_ip, target_ip, count=4):
        return PingUtility.ping_test(source_ip, target_ip, count)

    def toggle_device(self, device_id, status):
        # Update device online/offline status in DB
        conn = SubnetModel.get_all()
        from database.database import get_db_connection
        c = get_db_connection()
        c.execute("UPDATE devices SET status = ? WHERE id = ?", (status, device_id))
        c.commit()
        c.close()
        return {"device_id": device_id, "status": status}
