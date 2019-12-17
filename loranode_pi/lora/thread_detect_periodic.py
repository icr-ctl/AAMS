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
data_pkt_delay = 1.0

obj_ids = [0,0,0,0,0]
confs = [0,0,0,0,0]
def load_labels(path):
    p = re.compile(r'\s*(\d+)(.+)')
    with open(path, 'r', encoding='utf-8') as f:
       lines = (p.match(line).groups() for line in f.readlines())
       return {int(num): text.strip() for num, text in lines}

# drawing function for debugging purposes
def append_objs_to_img(cv2_im, objs, labels):
    height, width, channels = cv2_im.shape
    for obj in objs:
        x0, y0, x1, y1 = obj.bounding_box.flatten().tolist()
        x0, y0, x1, y1 = int(x0*width), int(y0*height), int(x1*width), int(y1*height)
        percent = int(100 * obj.score)
        label = '%d%% %s' % (percent, labels[obj.label_id])

        cv2_im = cv2.rectangle(cv2_im, (x0, y0), (x1, y1), (0, 255, 0), 2)
        cv2_im = cv2.putText(cv2_im, label, (x0, y0+30),
                             cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 0, 0), 2)
    return cv2_im

def detection():
    global obj_ids
    global confs
    # Initialize Coral Engine
    modelfile = 'models/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite'
    labelfile = 'models/coco_labels.txt'
    thresh = 0.0
    topk = 40

    print("[INFO] loading labels & engine...")
    labels = load_labels(labelfile)
    obj_id = len(labels)
    engine = DetectionEngine(modelfile)
    cap = cv2.VideoCapture(0)
    time.sleep(2.0)

    print("[INFO] looping over frames...")
    while cap.isOpened():
        ret, frame = cap.read()
        cv2_im = cv2.resize(frame, None, fx=0.5, fy=0.5)
        pil_im = Image.fromarray(cv2_im)
        objs = engine.detect_with_image(pil_im, threshold=thresh,
                            keep_aspect_ratio=True, relative_coord=True,
                            top_k=topk)

        # non-maximum suppression from opencv's DNN module
        bboxes = []
        scores = []
        score_thresh = 0.0
        nms_threshold = 0.5
        for obj in objs:
            bboxes.append(obj.bounding_box.flatten().tolist())
            scores.append(float(obj.score))
        indices = cv2.dnn.NMSBoxes(bboxes, scores, score_thresh,
                nms_threshold)

        print("num objects: " + str(len(objs)) + " and num left: " + str(len(indices)))
        leng = len(indices)
        if leng > 5:
            leng = 5
        for i in range(leng):
            idx = indices[i][0]
            label = labels[objs[idx].label_id]
            obj_ids[i] = objs[idx].label_id
            confs[i] = int(100*objs[idx].score)
            print(label + ": " + str(confs[i]))

        # cv2_im = append_objs_to_img(cv2_im, objs, labels)
        # drawing for debugging
        # cv2.imshow('frame', cv2_im)
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #    break

def send_pi_data(obj_ids, confs, pktnum, thousands):
    # Create data packet
    leng = (len(obj_ids)).to_bytes(2, byteorder='big')
    objs = b''
    for i in range(len(obj_ids)):
        objs += (obj_ids[i]).to_bytes(2, byteorder='big')
        objs += (confs[i]).to_bytes(2, byteorder='big')
    print(objs)
    pktnumber = (pktnum).to_bytes(2, byteorder='big')
    print("packet number: " + str(pktnum))
    thous = (thousands).to_bytes(2, byteorder='big')
    data_pkt = pktnumber + thous + leng + objs

    # Send data packet
    lora.send_data(data_pkt, len(data_pkt), lora.frame_counter)
    lora.frame_counter += 1
    display.fill(1)
    print('Data sent!')
    display.show()
    time.sleep(0.5)

def send_lora():
    global obj_ids
    global confs
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
        send_pi_data(obj_ids, confs, pktnum, thousands)
        time.sleep(data_pkt_delay)

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

