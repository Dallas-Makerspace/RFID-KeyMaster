from drivers.Interface.Interface import Interface
import pifacedigitalio
from exceptions.InvalidPositionException import InvalidPositionException
import atexit


class PiFaceInterface(Interface):
    def setup(self):
        # Turn off Interrupts
        pifacedigitalio.core.deinit()
        self.pifacedigital = pifacedigitalio.PiFaceDigital()
        atexit.register(self.reset_piface)
        
        return False
        
    def reset_piface(self):
        self.pifacedigital.init_board()
        
    def relay(self, position, value):
        position = int(position)

        if position >= 1 and position <= 2:
            self.output(position, value)
            return

        raise InvalidPositionException(
            "Pyface has no relay position " + str(position))

    def input(self, position):
        position = int(position)

        if position >= 1 and position <= 8:
            return self.pifacedigital.input_pins[position-1].value

        raise InvalidPositionException(
            "PiFace has no input position " + str(position))

    def output(self, position, value):
        position = int(position)

        if value:
            value = 1
        else:
            value = 0

        if position >= 1 and position <= 8:
            if value:
                self.pifacedigital.output_pins[position-1].turn_on()
            else:
                self.pifacedigital.output_pins[position-1].turn_off()
            return

        raise InvalidPositionException(
            "PiFace has no output position " + str(position))
