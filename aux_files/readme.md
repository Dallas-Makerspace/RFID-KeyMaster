By OZINDFW  

updated 9 OCT 25

Operation of this version of the KeyMaster RFID software has several requirements.  This file and the other directories contain information and files to meet those requirements.

If your configuration uses the PiGpioInterface driver, the user must be added to the gpio user group. The "pi" user is a default member of this group, all others must be added. 
Issue the folloowing command:
   sudo usermod -a -G gpio <username>

  UDEV

The USB card readers used are made by several manufacturers and report under slightly different names.  
The consequence of this is that swapping a failed reader out may require editing of the .ini file. The UDEV
rules file attempts to alias the reader to a symlink "RFID_Reader_x"  where X is 0 or 1 depending on the USB port used.  
This port dependency *should* allow the use of multiple readers and let one controller control more than one contactor. 

  Networking

The DMS implementation of interlocks rely on fixed IPs and names. This directory has a prototype dhcpd.conf configuration 
file to make this configuration easier. 

  BashMod

These two files are used to start, detect failure and restart the KeyMaster script. Keymaster is not started if already running 
(So SSH sessions don't spawn a second process.) 

  WiFi
  
This file improves Pi Zero W Wifi stability. Copy brcmfmac.conf to /etc/modprode.d/

   SSH

This change to SSHD is essential for PiZeroWs

