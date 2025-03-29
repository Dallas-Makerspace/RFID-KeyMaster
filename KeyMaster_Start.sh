#
#	this script is calld by .bashrc to monitor KeyMaster execution and 
#	restart if needed.
#
#   OZINDFW 20 SEP 2023, mod 22 OCT 2023, 10 March 2025
#

if pgrep -f "KeyMaster.py" >/dev/null 
then
	echo "KeyMaster Already Running"
	exit
else
	python KeyMaster.py |& tee -a  console.log &
	logger "Keymaster starting" 
	echo |& tee -a  console.log
	echo "Keymaster starting" |& tee -a  console.log
	date |& tee -a  console.log
	echo
fi
while [ true ] 
do
	if pgrep -f "KeyMaster.py" >/dev/null 
	then 
		sleep 2
	else 
		echo
		echo "Keymaster not running, restarting " |& tee -a  console.log
		date |& tee -a  console.log
		echo |& tee -a  console.log
		logger "Keymaster not running, restarting " 
		python KeyMaster.py |& tee -a  console.log &
	fi
done;
