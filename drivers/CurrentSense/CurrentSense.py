from drivers.Loadable import Loadable
from utils.Observer import Observable

class CurrentSense(Loadable):
    def __init__(self, config, loader):
        super().__init__(config, loader)
        self.currentChangeNotifier = self.CurrentChangeNotifier()
        self.value = None

    def getValue(self):
        return self.value

    def observeCurrentChange(self, observer):
        self.currentChangeNotifier.addObserver(observer)

    def notifyCurrentChangeObservers(self, value):
        self.currentChangeNotifier.notifyObservers(value)

    class CurrentChangeNotifier(Observable):
        def notifyObservers(self, value):
            self.setChanged()
            Observable.notifyObservers(self, value)
