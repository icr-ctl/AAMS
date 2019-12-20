What we want: a script that takes real time video and displays inference as well as
    captures a video. This means that the script WILL skip frames, because inference
    time on my computer is currently ~1 sec for normal weights and ~600 ms for tiny yolo

Currently:

- yolo_vid_opencv.py is NONthreaded and it works.
    - on built in webcam, runs in real time (skips frames) as intended
    - on IP webcam, does NOT skip frames and so lags behind realtime severely.

- q_vid.py is THREADED and it works
    - on built in webcam, runs in real time with a bit of delay.
