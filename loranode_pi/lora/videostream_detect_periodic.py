import os
import threading
import time

# Imports for lora
import subprocess
import busio
from digitalio import DigitalInOut, Direction, Pull
import board
# Import thte SSD1306 module.
import adafruit_ssd1306
# Import Adafruit TinyLoRa
from adafruit_tinylora.adafruit_tinylora import TTN, TinyLoRa

# Imports for detection:
import cv2
from PIL import Image
from threading import Thread
from queue import LifoQueue
import re
from edgetpu.detection.engine import DetectionEngine

# Create the I2C interface.
i2c = busio.I2C(board.SCL, board.SDA)
# 128x32 OLED Display
display = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c, addr=0x3c)
# Clear the display.
display.fill(0)
display.show()
width = display.width
height = display.height

# TinyLoRa Configuration
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = DigitalInOut(board.CE1)
irq = DigitalInOut(board.D22)
rst = DigitalInOut(board.D25)

# Gateway Device Address, 4 Bytes, MSB
devaddr = bytearray([0x00, 0x79, 0xCD, 0x6D])
# Gateway Network Key, 16 Bytes, MSB
nwkey = bytearray([0x3d, 0x7a, 0x37, 0x74, 0x27, 0x53, 0x66, 0xda, 0x39, 0x61, 0x6f, 0xf4, 0x23, 0xbe, 0x97, 0x2e])
# Gateway Application Key, 16 Bytess, MSB
app = bytearray([0x4f, 0x5c, 0x0c, 0xb0, 0xd3, 0x2a, 0x80, 0x91, 0x54, 0x46, 0x67, 0x54, 0x2d, 0x19, 0x36, 0x52])
# Initialize ThingsNetwork configuration
gway_config = TTN(devaddr, nwkey, app, country='US')
# Initialize lora object
lora = TinyLoRa(spi, cs, irq, rst, gway_config)
lora.set_datarate("SF10BW125")
# time to delay periodic packet sends (in seconds)
data_pkt_delay = 5.0

def send_pi_data(obj_id, conf, pktnum, thousands):
    # Send data packet
    bobj_id = (obj_id).to_bytes(2, byteorder='big')
    #print("object id: " + str(obj_id))
    bconf = (conf).to_bytes(2, byteorder='big')
    print("conf: " + str(conf))
    pktnumber = (pktnum).to_bytes(2, byteorder='big')
    print("packet number: " + str(pktnum))
    thous = (thousands).to_bytes(2, byteorder='big')
    data_pkt = bobj_id + bconf + pktnumber + thous
    lora.send_data(data_pkt, len(data_pkt), lora.frame_counter)
    lora.frame_counter += 1
    display.fill(1)
    print('Data sent!')
    display.show()
    time.sleep(0.5)

obj_id = 0
conf = 0
capfps = 0
capwid = 0
caphei = 0
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

def load_labels(path):
    p = re.compile(r'\s*(\d+)(.+)')
    with open(path, 'r', encoding='utf-8') as f:
       lines = (p.match(line).groups() for line in f.readlines())
       return {int(num): text.strip() for num, text in lines}

def detection():
    global obj_id
    global conf
    # Initialize Coral Engine
    modelfile = 'models/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite'
    labelfile = 'models/coco_labels.txt'
    thresh = 0.4
    topk = 3

    print("[INFO] loading labels & engine...")
    labels = load_labels(labelfile)
    obj_id = len(labels)
    engine = DetectionEngine(modelfile)
    vs = VideoStream().start()
    time.sleep(2.0)

    print("[INFO] looping over frames...")
    while vs.more():
        frame = vs.read()
        #vs.clearQ()
        cv2_im = cv2.resize(frame, None, fx=0.5, fy=0.5)
        pil_im = Image.fromarray(cv2_im)
        objs = engine.detect_with_image(pil_im, threshold=thresh,
                            keep_aspect_ratio=True, relative_coord=True,
                            top_k=topk)

        print("num objects: ", len(objs))
        for obj in objs:

            # drawing functions for debugging
            #box = obj.bounding_box.flatten().astype("int")
            #(startX, startY, endX, endY) = box
            # cv2.rectangle(cv2_im, (startX, startY), (endX, endY), (0, 255, 0), 2)
            #y = startY - 15 if startY - 15 > 15 else startY + 15
            #text = "{}: {:.2f}%".format(label, obj.score * 100)
            #cv2.putText(cv2_im, text, (startX, y),
            #cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            label = labels[obj.label_id]
            if label == "person":
                print("PERSON FOUND")
            obj_id = obj.label_id
            conf = int(100*obj.score)

        if len(objs) >= 0:
            print(labels[obj_id])
        else:
            obj_id = 0
        
        # drawing for debugging
        #cv2.imshow('frame', cv2_im)
        #if cv2.waitKey(1) & 0xFF == ord('q'):
        #    break


def send_lora():
    global obj_id
    global conf
    pktnum = 0
    thousands = 0
    while True:
        packet = None
        # draw a box to clear the image
        display.fill(0)
        display.show()

        pktnum += 1
        if pktnum >= 999:
            pktnum = 0
            thousands += 1
        
        print()
        print("Sending periodic data...")
        time.sleep(0.5)
        send_pi_data(obj_id, conf, pktnum, thousands)
        time.sleep(0.5)

        display.fill(0)
        display.show()
        time.sleep(.1)

if __name__=='__main__':
    t1 = threading.Thread(target=detection)
    t2 = threading.Thread(target=send_lora)
    t1.start()
    t2.start()

    t1.join()
    t2.join()

