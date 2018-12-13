from drivers.Loadable import Loadable

class CurrentSense(Loadable):
    _events_ = ['current_change']

    def __init__(self, config, loader):
        super().__init__(config, loader)
        self.value = None

    def getValue(self):
        return self.value

