from drivers.Loadable import Loadable
from utils.Observer import Observable

class CabinetSense(Loadable):
    def __init__(self, config, loader):
        super().__init__(config, loader)
        self.CabinetChangeNotifier = self.CabinetChangeNotifier()
        self.value = "none"

    def getValue(self):
        return self.value

    def observeCabinetChange(self, observer):
        self.CabinetChangeNotifier.addObserver(observer)

    def notifyCabinetChangeObservers(self, value):
        self.CabinetChangeNotifier.notifyObservers(value)

    class CabinetChangeNotifier(Observable):
        def notifyObservers(self, value):
            self.setChanged()
            Observable.notifyObservers(self, value)
