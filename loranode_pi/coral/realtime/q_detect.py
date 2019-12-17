'''
Multithreaded realtime detection uses a VideoStream class
For some reason, inference time is slower than gstreamer.
'''
from edgetpu.detection.engine import DetectionEngine
from PIL import Image
import argparse
import imutils
from threading import Thread
from queue import LifoQueue
import time
import cv2

# default confidence threshold is 0.4
ap = argparse.ArgumentParser()
ap.add_argument("-m", "--model", 
        default="models/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite", 
        help="path to TensorFlow Lite object detection model")
ap.add_argument("-l", "--labels",
        default="models/coco_labels.txt",
        help="path to labels file")
ap.add_argument("-c", "--confidence", type=float, default=0.4,
            help="minimum probability to filter weak detections")
args = vars(ap.parse_args())

# Video Stream class, creates a LIFO queue
class VideoStream:
    # initialize the file video stream
    def __init__(self, queueSize=128):

        global capfps
        global capwid 
        global caphei
        cap = cv2.VideoCapture(0)
        capfps = cap.get(cv2.CAP_PROP_FPS)
        capwid = round(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        caphei = round(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.stream = cap
        self.stopped = False                                                                                                                
        # initialize the queue 
        self.Q = LifoQueue(maxsize=queueSize)                       

    # thread to read frames from stream
    def start(self):
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self
    
    def update(self):                    
        while True:
            if self.stopped:
                return
            if not self.Q.full():
                # read the next frame from the file
                (grabbed, frame) = self.stream.read()
                
                # stop video if end of video file
                if not grabbed:
                    self.stop()
                    return
                                                                    
                # add the frame to the queue
                self.Q.put(frame)

    def read(self):
        # return next frame in the queue
        return self.Q.get()                                                                
    def more(self):
        # return True if there are still frames in the queue
        return self.Q.qsize() > 0                                                                                                           
    def clearQ(self):
        # empty the queue so it doesn't hit max size
        with self.Q.mutex:
            self.Q.queue.clear()
        return self.Q.empty()

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True

# parse labels file, load into directory.
print("[INFO] parsing class labels...")
labels = {}
for row in open(args["labels"]):
    (classID, label) = row.strip().split(maxsplit=1)
    labels[int(classID)] = label.strip()
                 
# load the Google Coral object detection model
print("[INFO] loading Coral model...")
model = DetectionEngine(args["model"])
                  
# initialize the pi camera video stream`
vs = VideoStream().start()
time.sleep(2.0)

# loop over the frames from the video stream
print("[INFO] looping over frames...")
while vs.more():
    # grab the frame from the threaded video stream and resize it
    # to have a maximum width of 500 pixels
    # also, clear the queue
    frame = vs.read()
    # vs.clearQ()
    frame = cv2.resize(frame, None, fx=0.5, fy=0.5)
    orig = frame.copy()
                         
    # prepare the frame for object detection by converting (1) it
    # from BGR to RGB channel ordering and then (2) from a NumPy
    # array to PIL image format
    #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = Image.fromarray(frame)

    # make predictions on the input frame
    start = time.time()
    results = model.detect_with_image(frame, threshold=args["confidence"],
            keep_aspect_ratio=True, relative_coord=False)
    end = time.time()
    print("Detection time: " + str(end-start))

    # loop over the results
    for r in results:
        # extract the bounding box and box and predicted class label
        box = r.bounding_box.flatten().astype("int")
        (startX, startY, endX, endY) = box
        label = labels[r.label_id]
        
        # draw the bounding box and label on the image
        cv2.rectangle(orig, (startX, startY), (endX, endY),
                (0, 255, 0), 2)
        y = startY - 15 if startY - 15 > 15 else startY + 15
        text = "{}: {:.2f}%".format(label, r.score * 100)
        cv2.putText(orig, text, (startX, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                                                                    
    # show the output frame and wait for a key press
    cv2.imshow("Frame", orig)
    key = cv2.waitKey(1) & 0xFF                               
    # if the `q` key was pressed, break from the loop
    if key == ord("q"):
        break                                                                        
cv2.destroyAllWindows()
vs.stop()

