There are two files are used to start, detect failure and restart the KeyMaster script. 

Keymaster is not started if already running (So SSH sessions don't spawn a second process)

Append the content of *bashrc-addendum.bash* to the *.bashrc* file in the KeyMaster home directory

make *KeyMaster_Start.sh* in the KeyMaster home directory exectuable by running 

     chmod +x KeyMaster_Start.sh
