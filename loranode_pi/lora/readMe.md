Quick file descriptions:
	- rfm9x_check.py: quick test that the bonnet is working.
	should display "Ada" "Fruit" "Radio" when pressing A B C

	- loradata.py: quick test that the lora bonnet can send lora data. 
	uses the buttons. should display "sent button _"

	- font5x8.bin: font file required to display text on LCD screen
	
	- font_periodicdata.py: sends periodic lora packets, but uses
	font file to display messages (doesn't work w/ crontab)
	otherwise same as cpperiodic.py

	- bonnet_p2p.py: sends data to another lora bonnet if one exists.
	- videostream_detect_periodic.py: realtime detection 
	using threading and the VideoStream class
	otherwise very similar to thread_detect_periodic.py

Important files:
	- cpperiodic.py: this is what starts up on crontab.
	periodically send lora packets when booted

	- detect_periodic.py: realtime detection w/ coral & rpicamera.
	periodically sends detections over lora.
	
	- thread_detect_periodic.py: realtime detection w/ coral.
	utilizes multithreading. periodically sends data over lora

	- full.py: does the same thing as ^thread_detect_periodic.py. 
	HOWEVER, sends an email when giraffe detected with conf > 75%,
	up to 1 email every 5 minutes. 
	Also, saves a local snapshot of the instant anything is detected
	w/ conf > 75%, up to 1 every 5 minutes.

