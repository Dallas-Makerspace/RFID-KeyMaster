These two files are used to start, detect failure and restart the KeyMaster script. 

Keymaster is not started if already running (So SSH sessions don't spawn a second process)

Append the content of *bashrc-addendum.bash* to the *.bashrc* file in the KeyMaster home directory

copy *KeyMaster_Start.sh* to the KeyMaster home directory and make it exectuable by running 

     chmod +x KeyMaster_Start.sh
