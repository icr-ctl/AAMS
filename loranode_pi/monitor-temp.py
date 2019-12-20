import os
import time

def measure_temp():
        temp = os.popen("vcgencmd measure_temp").readline()
        temp = temp.replace("temp=","")
        return float(temp.strip().strip("'C")) 

while True:
        temp = measure_temp()
        print(temp)
        if temp >= 80:
            print("IT IS GETTING HOT")
            for i in range(150):
                print("HOT HOT HOT HOT HOT HOT HOT HOT HOT HOT HOT HOT HOT HOT HOT HOT")
        time.sleep(120)
