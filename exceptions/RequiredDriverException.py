

class RequiredDriverException(Exception):
    def __init__(self, driver_type):
        super(RequiredDriverException, self).__init__("Could not find required driver type " + str(driver_type))
