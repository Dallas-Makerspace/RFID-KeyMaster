from importlib import import_module

class Loader:
    def __init__(self, config):
        self.drivers = {}
        self.config = config

    def getDriver(self, driver_type):
        if driver_type in self.drivers:
            return self.drivers[driver_type]
        return None

    def getDrivers(self):
        return self.drivers.values()

    def loadDriver(self, driver_type, driver):
        #print("Attempting to load ", driver_type, ", ", driver)
        module = import_module(driver)
        driver_class = getattr(module, driver)
 
        if driver_type not in self.drivers:
            self.drivers[driver_type] = None

        # if no config in config file, give empty dict
        if driver not in self.config.sections():
            driver_config = {}
        else:
            driver_config = dict(self.config.items(driver))

        # instantate driver class (config, loader)
        driver_instance = driver_class(driver_config, self)

        # append instance to driver dict
        self.drivers[driver_type] = driver_instance

        return driver_instance
