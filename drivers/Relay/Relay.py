from drivers.Loadable import Loadable
import time


class Relay(Loadable):
    """
    Driver for a single relay
    """

    def setup(self):
        """
        Setup for Relay Module

        :return: Returns true to enable threaded run method 
        """
        self.interface = self.getDriver('relay_interface')
        self.pin = self.config['interface_position']

        return False

    def on(self):
        """ Turns on relay

        :return: None
        """
        self.interface.relay(self.pin, 1)

    def off(self):
        """ Turn off relay

        :return: None
        """
        self.interface.relay(self.pin, 0)
