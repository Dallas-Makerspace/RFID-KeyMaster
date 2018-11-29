import threading
from exceptions.RequiredDriverException import RequiredDriverException

class Loadable(threading.Thread):
    def __init__(self, config, loader):
        self.config = config
        self.loader = loader
        super().__init__()

    def setup(self):
        return False

    def getDriver(self, driver_type):
        driver = self.loader.getDriver(driver_type)
        if driver == None:
            raise RequiredDriverException(driver_type)  
        return driver  
