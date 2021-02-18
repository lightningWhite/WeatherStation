# Argent Rain Sensor
#
# This file interfaces with the rain sensor to calculate how much rain has
# fallen in inches. It counts how many times the bucket has tipped, where each
# bucket tip signifies 0.011 inches of rain.
#
# Ensure the following connections to the Raspberry Pi 3 Model B:
#
# Pin 3 on the RJ11 connector to Ground
# Pin 4 on the RJ11 connector to BCM 6

from gpiozero import Button
import time

rain_sensor = Button(6)
BUCKET_SIZE = 0.011  # Inches per bucket tip
LOG_INTERVAL = 900  # How often to log in seconds (15 min)
count = 0
precipitation = 0


def bucket_tipped():
    global count
    global precipitation
    count = count + 1
    precipitation = count * BUCKET_SIZE
    print("tipped")


def reset_rainfall():
    global count
    count = 0


rain_sensor.when_pressed = bucket_tipped

while True:
    print(precipitation)
    time.sleep(LOG_INTERVAL)
