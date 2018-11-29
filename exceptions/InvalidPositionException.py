

class InvalidPositionException(Exception):
    def __init__(self, position):
        super(InvalidPositionException, self).__init__("There is no pin position for " + str(position))
