#
#	this script is calld by .bashrc to monitor KeyMaster execution and 
#	restart if needed.
#
#   OZINDFW 20 SEP 2023, mod 22 OCT 2023
#

if pgrep -f "KeyMaster.py" >/dev/null 
then
	echo "KeyMaster Already Running"
	exit
else
	python KeyMaster.py & 
	logger "Keymaster starting" 
	echo
	echo "Keymaster starting"
	date
	echo
fi
while [ true ] 
do
	if pgrep -f "KeyMaster.py" >/dev/null 
	then 
		sleep 2
	else 
		echo
		echo "Keymaster not running, restarting " 
		date 
		echo
		logger "Keymaster not running, restarting " 
		python KeyMaster.py &
	fi
done;
