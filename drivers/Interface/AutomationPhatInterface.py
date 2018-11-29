import automationhat
from exceptions.InvalidPositionException import InvalidPositionException


class AutomationPhat:

    def __init__(self):
        pass

    def relay(self, position, value):
        position = int(position)

        if value:
            value = 1
        else:
            value = 0

        if position == 1:
            automationhat.relay.one.write(value)

        raise InvalidPositionException(
            "Automation Phat has no relay position " + str(position))

    def input(self, position):
        position = int(position)

        if position == 1:
            return automationhat.input.one.read()
        elif position == 2:
            return automationhat.input.two.read()
        elif position == 3:
            return automationhat.input.three.read()

        raise InvalidPositionException(
            "Automation Phat has no input position " + str(position))

    def output(self, position, value):
        position = int(position)

        if value:
            value = 1
        else:
            value = 0

        if position == 1:
            return automationhat.output.one.write(value)
        elif position == 2:
            return automationhat.output.two.write(value)
        elif position == 3:
            return automationhat.output.three.write(value)

        raise InvalidPositionException(
            "Automation Phat has no output position " + str(position))
