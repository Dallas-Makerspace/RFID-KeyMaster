from drivers.Loadable import Loadable

class RFID(Loadable):
    _events_ = ['swipe']

    def __init__(self, config, loader):
        super().__init__(config, loader)

