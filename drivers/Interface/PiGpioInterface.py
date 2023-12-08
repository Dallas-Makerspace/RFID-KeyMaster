#
# Modified from PiFaceInterface class
#
#   By Rich Osman, 23 November 2023
#   Untested, and the coder is uninformed. 
#
#   The setup is complicated in attempt to retain compatibility with 
#   PiFace interface code
#
#  2Bdo
#    consider converting to BOARD pin numbering (as opposed to GPIO/bcm)
#    consider adding PWM output for the four pins that support it. 
#        which would be useful for indicator intensity control and color 
#        seelction/mixing
#

##################################################################################
#
#                           NOTE
#
# In order to use the GPIO ports your user must be a member of the gpio group. 
# The pi user is a member by default, other users need to be added manually.
#  sudo usermod -a -G gpio <username>
#
##################################################################################

import os  # is this really needed?
import logging  # want to add logging when more stable
import time     # is this really needed??
import configparser  # required to setup I/O 
import RPi.GPIO as gpio

import inspect 

from drivers.Interface.Interface import Interface

from exceptions.InvalidPositionException import InvalidPositionException

import atexit

class PiGpioInterface(Interface):

#
#   PiGpioInterface.PinTranslate is used to convert .ini file IO assignments to
#   GPIO BCM numerical values. 
#
#   The Limited dictionary is restricted to those GPIOs that are only
#   GPIO functions where the FullDict dictionary contains all pins 
#   including those that have alternate uses like serial or I2C ports.
#

    PinTranslate = {    # Limited
        "2":5, "GPIO5" : 5, "PIN29" : 5, "GPIO6" : 6, "PIN31" : 6,
        "GPIO16" : 16, "PIN36" : 16, "GPIO17" : 17, "PIN11" : 17,
        "GPIO22" : 22, "PIN15" : 22, "GPIO23" : 23, "PIN16" : 23,
        "GPIO24" : 24, "PIN18" : 24, "GPIO25" : 25, "PIN22" : 25,
        "GPIO26" : 26, "PIN37" : 26, "GPIO27" : 27, "PIN13" : 27
}

# PinTranslate = {  # Full
    # "GPIO5" : 5, "PIN29" : 5, "GPIO6" : 6, "PIN31" : 6,
    # "GPIO16" : 16, "PIN36" : 16, "GPIO17" : 17, "PIN11" : 17,
    # "GPIO22" : 22, "PIN15" : 22, "GPIO23" : 23, "PIN16" : 23,
    # "GPIO24" : 24, "PIN18" : 24, "GPIO25" : 25, "PIN22" : 25,
    # "GPIO26" : 26, "PIN37" : 26, "GPIO27" : 27, "PIN13" : 27,
    # "GPIO2" : 2, "PIN3" : 2, "GPIO3" : 3, "PIN5" : 3,
    # "GPIO4" : 4, "PIN7" : 4, "GPIO7" : 7, "PIN26" : 7,
    # "GPIO8" : 8, "PIN24" : 8, "GPIO9" : 9, "PIN21" : 9,
    # "GPIO10" : 10, "PIN19" : 10, "GPIO11" : 11, "PIN23" : 11,
    # "GPIO12" : 12, "PIN32" : 12, "GPIO13" : 13, "PIN33" : 13,
    # "GPIO14" : 14, "PIN8" : 14, "GPIO15" : 15, "PIN10" : 15,
    # "GPIO18" : 18, "PIN12" : 18, "GPIO19" : 19, "PIN35" : 19,
    # "GPIO20" : 20, "PIN38" : 20, "GPIO21" : 21, "PIN40" : 21
# }

#
#   IOAssignment is used to track GPIO assignment as input or output 
#   and prevent redundant and conflicting allocation of GPIO pins. 
#
#   Keys are GPIO numbers and values are: "U" for unassigned, 
#   "I" for input, and "O" for output
#

    IOAssignment = {
        2: "U", 3: "U", 4: "U", 5: "U", 6: "U", 7: "U", 8: "U", 
        9: "U", 10: "U", 11: "U", 12: "U", 13: "U", 14: "U", 15: "U", 
        16: "U", 17: "U", 18: "U", 19: "U", 20: "U", 21: "U", 22: "U", 
        23: "U", 24: "U", 25: "U", 26: "U", 27: "U"
    }
    
    def checkConfigPin(self,position,iou):
        
        bcm = None

        bcm = PiGpioInterface.PinTranslate.get(position) 
            
        if bcm == None:
            raise InvalidPositionException(
                "\n\nPosiiton GPIO",position," (",bcm,") "
                " Not available for assignment)\n\n")
        
        elif PiGpioInterface.IOAssignment.get(bcm) == iou:
            pass
        
        elif PiGpioInterface.IOAssignment.get(bcm) == "U":
        
            if iou == "I":
                gpio.setup(bcm, gpio.IN, gpio.PUD_UP)
                PiGpioInterface.IOAssignment.update({bcm : "I"})
                
            elif iou == "O":
                gpio.setup(bcm, gpio.OUT)
                PiGpioInterface.IOAssignment.update({bcm : "O"})
                
            else:
                print ("\n\nERROR: Do not recognize IO type ",iou,
                    " for GPIO",bcm,"\n\n")
                    
        else:   # already assigned something else
            bcm = None
            logging.debug("ERROR: IO Assignment Conflict for",function,
                " requested ",position," as ",iou,
                " and is already set to ",PiGpioInterface.IOAssignment.get(bcm))
        
        return bcm
           
    def reset_gpio(self):
        gpio.cleanup()
    
    def setup(self): 

        gpio.setmode(gpio.BCM)
        
        # can probably just refernce gpio.cleanup directly
        
        atexit.register(self.reset_gpio) 

    
        return True
        
       
    def input(self, position):

        return gpio.input(self.checkConfigPin(position,"I"))
        

    def output(self, position, value):
    
        if value > 0.1: value = 1
    
        gpio.output(self.checkConfigPin(position,"O"),value)

        return True
        

#   We can we just alias relay to output

    relay = output
    

        
        
