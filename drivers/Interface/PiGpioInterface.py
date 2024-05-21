#
# Modified from PiFaceInterface class
#
#  By Rich Osman, 3 January 2024
#  Functional, but not thoroughly tested 
#
#  The setup is complicated in an attempt to retain compatibility with 
#  legacy PiFace interface code. 
#
# The PiFace board pre-assigns input and outputs, so no iniitialization 
# is provided and logic sense is fixed.
#
# The PiFace pre-assigns two relay positions that we must use GPIOs for.
#
# The PiFace inverts input data and outputs are open collector and active 
# low, so GPIO must be inverted for copmatibility. I'm adding the option 
# of specifying logic sense to allow that flexibility in future revisions 
# and applicaitons. 
#
# 2Bdo
#  consider adding PWM output for the four pins that support it. 
#    which would be useful for indicator intensity control and color 
#    seelction/mixing
#

##################################################################################
#
#              NOTE
#
# In order to use the GPIO ports your user must be a member of the gpio group. 
# The pi user is a member by default, other users need to be added manually.
#
#  sudo usermod -a -G gpio <username>
#
##################################################################################

import logging # want to add logging when more stable
import configparser # required to setup I/O 
import RPi.GPIO as gpio

from drivers.Interface.Interface import Interface

from exceptions.InvalidPositionException import InvalidPositionException

import atexit

class PiGpioInterface(Interface):

#
#  PiGpioInterface.PinTranslate is used to convert .ini file IO assignments to
#  pin number numerical values. 
#

    PinTranslate = {
        "pin3" : 3, "gpio2" : 3, "pin5" : 5, "gpio3" : 5, "pin7" : 7,
        "gpio4" : 7, "pin8" : 8, "gpio14" : 8, "pin10" : 10,
        "gpio15" : 10, "pin11" : 11, "gpio17" : 11, "pin12" : 12,
        "gpio18" : 12, "pin13" : 13, "gpio27" : 13, "pin15" : 15,
        "gpio22" : 15, "pin16" : 16, "gpio23" : 16, "pin18" : 18,
        "gpio24" : 18, "pin19" : 19, "gpio10" : 19, "pin21" : 21,
        "gpio9" : 21, "pin22" : 22, "gpio25" : 22, "pin23" : 23,
        "gpio11" : 23, "pin24" : 24, "gpio8" : 24, "pin26" : 26,
        "gpio7" : 26, "pin29" : 29, "gpio5" : 29, "pin31" : 31,
        "gpio6" : 31, "pin32" : 32, "gpio12" : 32, "pin33" : 33,
        "gpio13" : 33, "pin35" : 35, "gpio19" : 35, "pin36" : 36,
        "gpio16" : 36, "pin37" : 37, "gpio26" : 37, "pin38" : 38,
        "gpio20" : 38, "pin40" : 40, "gpio21" : 40
    }

#
#  IOAssignment is used to track GPIO assignment as input or output 
#  and prevent redundant and conflicting allocation of GPIO pins. 
#
#  Keys are pin numbers and values are: "U" for unassigned, 
#  "I" for input, and "O" for output
#

    IOAssignment = {
        3 : "U", 5 : "U", 7 : "U", 8 : "U", 10 : "U", 11 : "U", 12 : "U",
        13 : "U", 15 : "U", 16 : "U", 18 : "U", 19 : "U", 21 : "U",
        22 : "U", 23 : "U", 24 : "U", 26 : "U", 29 : "U", 31 : "U",
        32 : "U", 33 : "U", 35 : "U", 36 : "U", 37 : "U", 38 : "U",
        40 : "U"
  }

#
#   checkConfigPin 
#
#    accepts a string with a pin description (GPIO or PIN number) and
#        optionally a logic sense (inverting or non-inverting)
#    and a pin type ("I" for input; "O" for output)
#    
#    Checks to see if the pin is assignable with PinTranslate and 
#        converts it to a valid pin number
#
#    Checks to see if it's already been assigned in IOAssignment and 
#    whether that assignment is consistent with the current check.  If
#    unassigned, assigns it.
#    
#    Determines whether to pin should be inverted (inverting) 
#    or not (non-inverting), defaults to inverting.
#    
#    Returns a tuple with the physical GPIO pin number and 
#    boolean logic sense (inverting = true)
#

    def checkConfigPin(self,position,iou):

# seperate configuration arguments and strip whitespace.  
        position = position.split(", ")
        
        position[0]= position[0].strip()
        position[1]= position[1].strip()

        invert = True
        
        if len(position) > 2:
            raise InvalidPositionException(
            "\nPosition GPIO",position," has too many arguments \n")
            
        if len(position) == 0:
            raise InvalidPositionException(
            "\nPosition GPIO",position," has too few arguments \n")
        
        if len(position) == 2 and str.lower(position[1]) == 'non-inverting':
            invert = False
 
        iopin = None

        iopin = PiGpioInterface.PinTranslate.get(str.lower(position[0]))

        if iopin == None:
        
            error = "Position GPIO",position," (",iopin,") Not available for assignment)\n"
        
            raise InvalidPositionException(error)
    
        elif PiGpioInterface.IOAssignment.get(iopin) == iou:
            
            pass
    
        elif PiGpioInterface.IOAssignment.get(iopin) == "U":
    
            if iou == "I":
                gpio.setup(iopin, gpio.IN, gpio.PUD_UP)
                PiGpioInterface.IOAssignment.update({iopin : "I"})
            
            elif iou == "O":
                gpio.setup(iopin, gpio.OUT)
                PiGpioInterface.IOAssignment.update({iopin : "O"})
            
            else:
                error = "Do not recognize IO type "+iou+ "for GPIO"+iopin+"\n"
                raise InvalidPositionException(error)
          
        else:  # already assigned something else
            iopin = None
            logging.debug("ERROR: IO Assignment Conflict for",function,
                " requested ",position," as ",iou,
                " and is already set to ",PiGpioInterface.IOAssignment.get(iopin))

        return [iopin,invert]
      
    def reset_gpio(self):
        gpio.cleanup()
  
    def setup(self): 

        gpio.setmode(gpio.BOARD)
    
# can probably just reference gpio.cleanup directly
    
        atexit.register(self.reset_gpio)

        return True
    
    
    def input(self, position):
    
        pinconfig = self.checkConfigPin(position,"I")
        
        input = gpio.input(pinconfig[0])

        return pinconfig[1] ^ input

    def output(self, position, value):
    
#   some code provides values up to 255 expecting a PWM pin 
#       with an 8 bit counter
      
        if value > 0.1: value = 1  
        
        pinconfig = self.checkConfigPin(position,"O")

        ovalue = value ^ pinconfig[1]
        
        gpio.output(pinconfig[0],ovalue)

        return True
    

#  We can we just alias relay to output

    relay = output
#
# will add a pwm function to accomodate those routines that expect it 
#   some day 
  

    
    
