import cv2 as cv
import argparse
import numpy as np
import time
from threading import Thread
from queue import LifoQueue
import imutils

# Initialize the parameters
nmsThreshold = 0.4   #Non-maximum suppression threshold
inpWidth = 416       #Width of network's input image
inpHeight = 416      #Height of network's input image
capfps = 0
capwid = 0
caphei = 0

parser = argparse.ArgumentParser()
parser.add_argument("--conf", metavar="conf", type=float, default=0.3)
parser.add_argument("--output", metavar="outputFile", type=str, default="output.avi")
parser.add_argument("--classes", metavar="classesFile", type=str, required=True)
parser.add_argument("--cfg", metavar="cfgFile", type=str, required=True)
parser.add_argument("--weights", metavar="weightsFile", type=str, required=True)
parser.add_argument("-o", action="store_true", help="want original video file?")
parser.add_argument("-r", action="store_true", help="resize display?")
parser.add_argument("-w", action="store_true", help="built in webcam?")
args = parser.parse_args()

confThreshold = args.conf  #Confidence threshold

# Load names of classes
classesFile = args.classes
classes = None
with open(classesFile, 'rt') as f:
    classes = f.read().rstrip('\n').split('\n')
 
# Give the configuration and weight files for the model and load the network using them.
modelConfiguration = args.cfg
modelWeights = args.weights
 
net = cv.dnn.readNetFromDarknet(modelConfiguration, modelWeights)
net.setPreferableBackend(cv.dnn.DNN_BACKEND_OPENCV)
net.setPreferableTarget(cv.dnn.DNN_TARGET_CPU)

class VideoStream:
    def __init__(self, queueSize=128):
        # initialize the file video stream along with the boolean
        # used to indicate if the thread should be stopped or not
        global capfps
        global capwid 
        global caphei
        if (args.w):
            cap = cv.VideoCapture(0)
            capfps = cap.get(cv.CAP_PROP_FPS)
        else:
            cap = cv.VideoCapture("rtsp://admin:NyalaChow22@192.168.1.64/Streaming/Channels/3")
            capfps = 30
        capwid = round(cap.get(cv.CAP_PROP_FRAME_WIDTH))
        caphei = round(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
        self.stream = cap
        self.stopped = False
 
        # initialize the queue used to store frames read from
        # the video file
        self.Q = LifoQueue(maxsize=queueSize)

    def start(self):
        # start a thread to read frames from the file video stream
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        # keep looping infinitely
        while True:
            # if the thread indicator variable is set, stop the
            # thread
            if self.stopped:
                return
 
            # otherwise, ensure the queue has room in it
            if not self.Q.full():
                # read the next frame from the file
                (grabbed, frame) = self.stream.read()
 
                # if the `grabbed` boolean is `False`, then we have
                # reached the end of the video file
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
        with self.Q.mutex:
            self.Q.queue.clear()
        return self.Q.empty()

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True

# Webcam input
print("[INFO] starting video file thread...")
fvs = VideoStream().start()
time.sleep(1.0)

outputFile = args.output
origoutputFile = "orig_" + args.output
# Get the video writer initialized to save the output video
vid_writer = cv.VideoWriter(outputFile, cv.VideoWriter_fourcc('M', 'J', 'P', 'G'), capfps, (capwid,caphei))
if args.o:
    origvid_writer = cv.VideoWriter(origoutputFile, cv.VideoWriter_fourcc('M','J','P','G'), capfps, (capwid,caphei))
    print("*** Recording original video too...")
else:
    print("*** NOT recording original video!")
print("CAMERA FPS IS: " + str(capfps))
print("FRAME SHAPE IS w:" + str(capwid) + " h:" + str(caphei))

# Get the names of the output layers
def getOutputsNames(net):
    # Get the names of all the layers in the network
    layersNames = net.getLayerNames()
    # Get the names of the output layers, i.e. the layers with unconnected outputs
    return [layersNames[i[0] - 1] for i in net.getUnconnectedOutLayers()]

# Remove the bounding boxes with low confidence using non-maxima suppression
def postprocess(frame, outs):
    frameHeight = frame.shape[0]
    frameWidth = frame.shape[1]

    classIds = []
    confidences = []
    boxes = []
    # Scan through all the bounding boxes output from the network and keep only the
    # ones with high confidence scores. Assign the box's class label as the class with the highest score.
    classIds = []
    confidences = []
    boxes = []
    for out in outs:
        for detection in out:
            scores = detection[5:]
            classId = np.argmax(scores)
            confidence = scores[classId]
            if confidence > confThreshold:
                center_x = int(detection[0] * frameWidth)
                center_y = int(detection[1] * frameHeight)
                width = int(detection[2] * frameWidth)
                height = int(detection[3] * frameHeight)
                left = int(center_x - width / 2)
                top = int(center_y - height / 2)
                classIds.append(classId)
                confidences.append(float(confidence))
                boxes.append([left, top, width, height])

    # Perform non maximum suppression to eliminate redundant overlapping boxes with
    # lower confidences.
    indices = cv.dnn.NMSBoxes(boxes, confidences, confThreshold, nmsThreshold)
    for i in indices:
        i = i[0]
        box = boxes[i]
        left = box[0]
        top = box[1]
        width = box[2]
        height = box[3]
        drawPred(classIds[i], confidences[i], left, top, left + width, top + height)

# Draw the predicted bounding box
def drawPred(classId, conf, left, top, right, bottom):
    # Draw a bounding box.
    cv.rectangle(frame, (left, top), (right, bottom), (0, 0, 255))

    label = '%.2f' % conf

    # Get the label for the class name and its confidence
    if classes:
        assert(classId < len(classes))
        label = '%s:%s' % (classes[classId], label)

    #Display the label at the top of the bounding box
    labelSize, baseLine = cv.getTextSize(label, cv.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    top = max(top, labelSize[1])
    cv.putText(frame, label, (left, top), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255))

while fvs.more():
    tstart = time.time() 
    # get frame from the video
    frame = fvs.read()
    if args.o:
        origvid_writer.write(frame.astype(np.uint8))
    fvs.clearQ()
    frame = imutils.resize(frame, width=450)

    # Create a 4D blob from a frame.
    blob = cv.dnn.blobFromImage(frame, 1/255, (inpWidth, inpHeight), [0,0,0], 1, crop=False)
 
    # Sets the input to the network
    net.setInput(blob)
 
    # Runs the forward pass to get output of the output layers
    outs = net.forward(getOutputsNames(net))
 
    # Remove the bounding boxes with low confidence
    postprocess(frame, outs)
 
    # Put efficiency information. The function getPerfProfile returns the 
    # overall time for inference(t) and the timings for each of the layers(in layersTimes)
    t, _ = net.getPerfProfile()
    label = 'Inference time: %.2f ms' % (t * 1000.0 / cv.getTickFrequency())
    cv.putText(frame, label, (20, caphei-20), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255))
    vid_writer.write(frame.astype(np.uint8))
    if args.r:
        frame = imutils.resize(frame, width=450)
        cv.putText(frame, label, (20, caphei-20), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255))
    cv.imshow("Prediction", frame)
    if cv.waitKey(1) and 0xFF == ord('q'):
        break
    ttotal = time.time() - tstart
    print("Time to process frame: " + str(ttotal))



