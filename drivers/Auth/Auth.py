from drivers.Loadable import Loadable

class Auth(Loadable):
    _events_ = ['auth', 'auth_processing']

    def __init__(self, config, loader):
        super().__init__(config, loader)
