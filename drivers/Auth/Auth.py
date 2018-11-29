from drivers.Loadable import Loadable
from utils.Observer import Observable


class Auth(Loadable):
    def __init__(self, config, loader):
        super().__init__(config, loader)
        self.authNotifier = self.AuthNotifier()
        self.authProcessingNotifier = self.AuthProcessingNotifier()

    def observeAuth(self, observer):
        self.authNotifier.addObserver(observer)

    def observeAuthProcessing(self, observer):
        self.authProcessingNotifier.addObserver(observer)

    def notifyAuthObservers(self, user):
        self.authNotifier.notifyObservers(user)

    def notifyAuthProcessingObservers(self):
        self.authProcessingNotifier.notifyObservers()

    class AuthNotifier(Observable):
        def notifyObservers(self, user):
            self.setChanged()
            super().notifyObservers(user)

    class AuthProcessingNotifier(Observable):
        def notifyObservers(self):
            self.setChanged()
            super().notifyObservers(None)
