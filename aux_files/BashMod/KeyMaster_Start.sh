#
#	this script is calld by .bashrc to monitor KeyMaster execution and 
#	restart if needed.
#
#   OZINDFW 20 SEP 2023, mod 10 March 2025
#

if pgrep -f "KeyMaster.py" >/dev/null 
then
	echo "KeyMaster Already Running"
	exit
else
	python KeyMaster.py &>> console.log &
	logger "Keymaster starting" 
	echo &>> console.log
	echo "Keymaster starting" &>> console.log
	date &>> console.log
	echo
fi
while [ true ] 
do
	if pgrep -f "KeyMaster.py" >/dev/null 
	then 
		sleep 2
	else 
		echo
		echo "Keymaster not running, restarting " &>> console.log
		date &>> console.log
		echo &>> console.log
		logger "Keymaster not running, restarting " 
		python KeyMaster.py &>> console.log &
	fi
done;
