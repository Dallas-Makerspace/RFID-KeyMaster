from drivers.Loadable import Loadable
import queue


class Controller(Loadable):
    def __init__(self, config, loader):
        super().__init__(config, loader)
