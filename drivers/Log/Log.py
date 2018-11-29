from drivers.Loadable import Loadable

class Log(Loadable):
    def auth(self, user):
        pass

    def engaged(self, status):
        pass

    def debug(self, message):
        pass

    def info(self, message):
        pass
    
    def error(self, message):
        pass

    def setup(self):
        return False
