#
# Modified from PiGpioInterface class
#
#   By Rich Osman, 29 August 2025
#   Untested, and the coder is uninformed. 
#

from drivers.Interface.Interface import Interface
import gpiod

#       Info
#       gpiod  https://github.com/aswild/python-gpiod   https://wiki.loliot.net/docs/lang/python/libraries/gpiod/python-gpiod-about/  
#       https://stackoverflow.com/questions/74352978/python-libgpiod-vs-gpiod-packages-in-linux   https://elinux.org/RPi_BCM2835_GPIOs


from exceptions.InvalidPositionException import InvalidPositionException
import atexit


class PiGpioDInterface(Interface):
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
import gpiod

from drivers.Interface.Interface import Interface

from exceptions.InvalidPositionException import InvalidPositionException

import atexit

class PiGpioDInterface(Interface):

#
#  PiGpioDInterface.PinTranslate is used to convert .ini file IO assignments to
#  GPIO numerical values. 
#

    PinTranslate = {
        "pin3" : 2, "gpio2" : 2, "bcm2" : 2, 
        "pin5" : 3, "gpio3" : 3, "bcm3" : 3, 
        "pin7" : 4, "gpio4" : 4, "bcm4" : 4, 
        "pin8" : 14, "gpio14" : 14, "bcm14" : 14, 
        "pin10" : 15, "gpio15" : 15, "bcm15" : 15, 
        "pin11" : 17, "gpio17" : 17, "bcm17" : 17, 
        "pin12" : 18, "gpio18" : 18, "bcm18" : 18, 
        "pin13" : 27, "gpio27" : 27, "bcm27" : 27, 
        "pin15" : 22, "gpio22" : 22, "bcm22" : 22, 
        "pin16" : 23, "gpio23" : 23, "bcm23" : 23, 
        "pin18" : 24, "gpio24" : 24, "bcm24" : 24, 
        "pin19" : 10, "gpio10" : 10, "bcm10" : 10, 
        "pin21" : 9, "gpio9" : 9, "bcm9" : 9, 
        "pin22" : 25, "gpio25" : 25, "bcm25" : 25, 
        "pin23" : 11, "gpio11" : 11, "bcm11" : 11, 
        "pin24" : 8, "gpio8" : 8, "bcm8" : 8, 
        "pin26" : 7, "gpio7" : 7, "bcm7" : 7, 
        "pin27" : 0, "gpio0" : 0, "bcm0" : 0, 
        "pin28" : 1, "gpio1" : 1, "bcm1" : 1, 
        "pin29" : 5, "gpio5" : 5, "bcm5" : 5, 
        "pin31" : 6, "gpio6" : 6, "bcm6" : 6, 
        "pin32" : 12, "gpio12" : 12, "bcm12" : 12, 
        "pin33" : 13, "gpio13" : 13, "bcm13" : 13, 
        "pin35" : 19, "gpio19" : 19, "bcm19" : 19, 
        "pin36" : 16, "gpio16" : 16, "bcm16" : 16

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
#    accepts a string with a pin description (GPIO, BCM, or PIN number) 
#       and optionally a logic sense (inverting or non-inverting)
#       and a pin type ("I" for input; "O" for output)
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

        iopin = PiGpioDInterface.PinTranslate.get(str.lower(position[0]))
        
#
#   Should add GPIOD gpiod.LineInfo checks here to avoid multiple user conflicts. 
#        

        if iopin == None:
        
            error = "Position GPIO",position," (",iopin,") Not available for assignment)\n"
        
            raise InvalidPositionException(error)
    
        elif PiGpioDInterface.IOAssignment.get(iopin) == iou:
            
            pass
    
        elif PiGpioDInterface.IOAssignment.get(iopin) == "U":
    
            if iou == "I":
                line=chip.get_line(iopin)
                line.request(consumer='PiGpioDInterface', type=gpiod.LINE_REQ_DIR_IN)
  
  #              gpio.setup(iopin, gpio.IN, gpio.PUD_UP)
  #              PiGpioInterface.IOAssignment.update({iopin : "I"})
            
            elif iou == "O":
                line=chip.get_line(iopin)
                line.request(consumer='PiGpioDInterface', type=gpiod.LINE_REQ_DIR_OUT)

  #              gpio.setup(iopin, gpio.OUT)
  #              PiGpioInterface.IOAssignment.update({iopin : "O"})
            
            else:
                error = "Do not recognize IO type "+iou+ "for GPIO"+iopin+"\n"
                raise InvalidPositionException(error)
          
        else:  # already assigned something else
            iopin = None
            logging.debug("ERROR: IO Assignment Conflict for",function,
                " requested ",position," as ",iou,
                " and is already set to ",PiGpioInterface.IOAssignment.get(iopin))

        return [iopin,invert]
      
    def reset_gpiod(self):
        
        chip.close()
  
    def setup(self): 

        chip = gpiod.Chip('gpiochip0')
    
        atexit.register(self.reset_gpio)

        return True
    
    def input(self, position):
    
        line = get_line(self.checkConfigPin(position,"I"))
 
 # pinconfig[1] determines logic sense of line
        
        return = get_value(line) ^ pinconfig[1] 

    def output(self, position, value):
    
#   some calling code provides values up to 255 expecting a PWM pin 
#       with an 8 bit counter - see final comment
      
        if value > 0.1: value = 1  
        else: value = 0
        
        line = get_line(self.checkConfigPin(position,"O"))

 # pinconfig[1] determines logic sense of line

        line.set_value(value ^ pinconfig[1])
        
        return True
    
#  We can we just alias relay to output
#       This is provided for compatibility with code written for the
#       obsolete PiFace interface still used in legaacy systems.

    relay = output
#
# may add a pwm function to accomodate those routines that expect it 
#   some day 
  
