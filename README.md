# RFID-KeyMaster
KeyMaster RFID Interlock for Raspberry Pi

Aux_files contains support files for KeyMaster Implementation on a raspberry Pi.

KeyMaster_Start.sh needs to be marked as executable. It's called by the modified Bashrc script on login. 

...
chmod +x KeyMaster_Start.sh
...

Keymaster is not started if already running (So SSH sessions don't spawn a second process)

Append the content of bashrc-addendum.bash in aux_files to the .bashrc file in the KeyMaster home directory
