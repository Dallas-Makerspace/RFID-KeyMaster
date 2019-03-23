from drivers.Loadable import Loadable
import queue


class Controller(Loadable):
    controller = "Controller"
    def __init__(self, config, loader):
        super().__init__(config, loader)
        self.controller = self.__class__.__name__
