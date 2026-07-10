class DeviceManager:

    def __init__(self):
        self.active_device = "laptop"

    def set_active_device(self, device):
        self.active_device = device

    def get_active_device(self):
        return self.active_device