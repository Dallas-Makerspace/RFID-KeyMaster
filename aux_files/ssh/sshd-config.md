This addition is critical for PiZeroWs

Edit

/etc/ssh/sshd_config

and add the line

IPQoS 0x00

Reference: https://raspberrypi.stackexchange.com/questions/143142/has-anyone-solved-raspberry-pi-zero-w-ssh-client-loop-send-disconnect-broken
