from importlib import import_module
import logging

class Loader:
    def __init__(self, config):
        self.drivers = {
            'common': {},
            'controllers': {}
        }
        self.config = config

    def getDriver(self, driver_name, controller=None):
        # Look for driver in controller
        if controller in self.drivers['controllers']:
            if driver_name in self.drivers['controllers'][controller]:
                return self.drivers['controllers'][controller][driver_name]

        # Look for driver in common
        if driver_name in self.drivers['common']:
            return self.drivers['common'][driver_name]

        return None

    def getCommonDrivers(self):
        return self.drivers['common'].values()    

    def getControllerDrivers(self, controller):
        return self.drivers['controllers'][controller].values()    

    def loadDriver(self, driver_name, driver_class_name, controller=None):
        #print("Attempting to load ", driver_name, ", ", driver)
        module = import_module(driver_class_name)
        driver_class = getattr(module, driver_class_name)
 
        # get config for driver
        # Look for config in Controllers
        driver_config = None
        if controller in self.config['controllers']:
            if driver_name in self.config['controllers'][controller]:
                driver_config = self.config['controllers'][controller][driver_name]

        if driver_config == None:
            # Look for driver in common
            if driver_name in self.config['common']:
                driver_config = self.config['common'][driver_name]
            else:
                raise Exception("Could not find config for driver: %s %s" % (controller, driver_name))

        # instantate driver class (config, loader)
        driver_instance = driver_class(driver_config, self)

        # append instance to driver dict

        # Look for driver in controller
        if controller == None:
            if driver_name not in self.drivers['common']:
                self.drivers['common'][driver_name] = driver_instance
            else:
                raise Exception("Driver already defined in common: %s" % driver_name)
        else:
            if controller not in self.drivers['controllers']:
                self.drivers['controllers'][controller] = {}

            if driver_name not in self.drivers['controllers'][controller]:
                self.drivers['controllers'][controller][driver_name] = driver_instance
            else:
                raise Exception("Driver already defined in controller: %s %s" % (controller, driver_name))

        return driver_instance
