import os
import threading
import time
import subprocess
import busio
from digitalio import DigitalInOut, Direction, Pull
import board
# Import thte SSD1306 module.
import adafruit_ssd1306
# Import Adafruit TinyLoRa
from adafruit_tinylora.adafruit_tinylora import TTN, TinyLoRa

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

# TTN Device Address, 4 Bytes, MSB
devaddr = bytearray([0x00, 0x79, 0xCD, 0x6D])
# TTN Network Key, 16 Bytes, MSB
nwkey = bytearray([0x3d, 0x7a, 0x37, 0x74, 0x27, 0x53, 0x66, 0xda, 0x39, 0x61, 0x6f, 0xf4, 0x23, 0xbe, 0x97, 0x2e])
# TTN Application Key, 16 Bytess, MSB
app = bytearray([0x4f, 0x5c, 0x0c, 0xb0, 0xd3, 0x2a, 0x80, 0x91, 0x54, 0x46, 0x67, 0x54, 0x2d, 0x19, 0x36, 0x52])
# Initialize ThingsNetwork configuration
gway_config = TTN(devaddr, nwkey, app, country='US')
# Initialize lora object
lora = TinyLoRa(spi, cs, irq, rst, gway_config)
lora.set_datarate("SF10BW125")
# 2b array to store sensor data
# data_pkt = bytearray(2)
# time to delay periodic packet sends (in seconds)
data_pkt_delay = 5.0

def send_pi_data(data):
    # data = int(data)
    # Encode payload as bytes
    # data_pkt[0] = (data >> 8) & 0xff
    # data_pkt[1] = data & 0xff
    # Send data packet
    data_pkt = (data).to_bytes(2, byteorder='big')
    print(data)
    print(data_pkt)
    lora.send_data(data_pkt, len(data_pkt), lora.frame_counter)
    lora.frame_counter += 1
    display.fill(0)
    display.text('Sent to Gateway!', 15, 15, 1)
    print('Data sent!')
    display.show()
    time.sleep(0.5)

pktnum = 0
while True:
    packet = None
    # draw a box to clear the image
    display.fill(0)
    display.text('RasPi LoRaWAN', 35, 0, 1)

    # get temperature
    temp = os.popen("vcgencmd measure_temp").readline()
    dat = int(float(temp.replace("temp=","").replace("'C", "")))
    pktnum += 1
    print("Packet number: " + str(pktnum))

    print("Sending periodic data...")
    display.fill(0)
    display.show()
    time.sleep(0.5)
    send_pi_data(dat)
    time.sleep(0.5)


    display.show()
    time.sleep(.1)

