from drivers.Loadable import Loadable
from abc import ABCMeta, abstractmethod
from utils.Observer import Observable


class RFID(Loadable):
    def __init__(self, config, loader):
        super().__init__(config, loader)
        self.scanNotifier = self.ScanNotifier()

    def observeScan(self, observer):
        self.scanNotifier.addObserver(observer)

    def notifyScanObservers(self, rfid_number):
        self.scanNotifier.notifyObservers(rfid_number)

    class ScanNotifier(Observable):
        def notifyObservers(self, rfid_number):
            self.setChanged()
            Observable.notifyObservers(self, rfid_number)
