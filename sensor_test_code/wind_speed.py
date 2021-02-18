# Argent Anemometer Sensor
#
# Reports the wind speed in miles per hour
#
# Ensure the following connections to the Raspberry Pi 3 Model B:
#
# Pin 3 on the RJ11 connector to Ground
# Pin 4 on the RJ11 connector to BCM 5

from gpiozero import Button
import math
import statistics
import time

CM_IN_A_MILE = 160934.4
SECS_IN_AN_HOUR = 3600

CALIBRATION = 2.3589722140805094

# How often the average wind speed and wind gust should be logged
LOG_INTERVAL = 5  # 900 # 15 Minutes in seconds
wind_interval = 5  # 30# How often in seconds to record the speed

wind_speed_sensor = Button(5)  # BCM 5
wind_count = 0  # Number of half rotations
radius_cm = 9.0  # Radius of the anemometer

# Store speeds in order to record wind gusts
store_speeds = []


def spin():
    global wind_count
    wind_count = wind_count + 1


def calculate_speed(time_sec):
    global wind_count
    circumference_cm = (2 * math.pi) * radius_cm
    rotations = wind_count / 2.0

    # Calculate the distance travelled by a cup in cm
    dist_mile = (circumference_cm * rotations) / CM_IN_A_MILE

    # Report the wind speed in miles per hour
    miles_per_sec = dist_mile / time_sec
    miles_per_hour = miles_per_sec * SECS_IN_AN_HOUR

    # The anemometer data sheet indicates that if the switch closes once per
    # second, a wind speed of 1.492 MPH should be reported
    # Multiply by the calibration factor to be accurate according to the
    # data sheet
    return miles_per_hour * CALIBRATION


def reset_wind():
    global wind_count
    wind_count = 0


# Call the spin function every half rotation
wind_speed_sensor.when_pressed = spin

while True:
    start_time = time.time()

    # Record the wind speed every 5 seconds, report the avg. and gust every
    # LOG_INTERVAL seconds
    while time.time() - start_time <= LOG_INTERVAL:
        reset_wind()
        time.sleep(wind_interval)
        final_speed = calculate_speed(wind_interval)
        store_speeds.append(final_speed)

    # Log the wind gust and the average speed over the LOG_INTERVAL
    wind_gust = max(store_speeds)
    wind_speed = statistics.mean(store_speeds)
    print(f"Avg. Wind Speed: {wind_speed}, Wind Gust: {wind_gust}")

    # Clear the recorded speeds so the gust can be updated during the next log period
    store_speeds.clear()
