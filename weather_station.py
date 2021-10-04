# Weather Station
#
# A basic weather data logging station controlled by a Raspberry Pi.
#
# Written by Daniel Hornberger


from gpiozero import Button
import bme280_sensor
import camera
import datetime
from influxdb import InfluxDBClient
import logger as logging
import math
import os
from pathlib import Path
from picamera import PiCamera
import shutil
import statistics
import subprocess
import sys
import time
import traceback
import wind_direction


# How often the sensor readings should be logged
LOG_INTERVAL = 900  # 15 Minutes in seconds
LOG_INTERVAL = 10  # 15 Minutes in seconds

# How often readings should be taken to form the average that will be logged
ACCUMULATION_INTERVAL = 10  # 10 seconds
#ACCUMULATION_INTERVAL = 5  # 10 seconds
ACCUMULATION_INTERVAL = 2  # 10 seconds

# Enable or disable the photos from being taken.
# If enabled, more disk space will be used.
PHOTOS_ENABLED = True

# When the disk has less than this amount of free storage in bytes,
# images will cease to be captured.
IMAGE_DISK_USAGE_THRESHOLD = 1000000000 # 1 GB

# When an image has an average grayscale brightness less than this value,
# images will not be saved to the disk. This is so images won't be taken
# during the night.
# TODO: This value may need further tuning after deployment and further testing
BRIGHTNESS_THRESHOLD = 20

# Issues occur unless only a single camera object is used for the duration of
# the program.
camera_obj = PiCamera()
camera_obj.resolution = (1024, 1024)
camera_obj.brightness = 50
camera_obj.rotation = 90 

###############################################################################
# InfluxDB Database Setup
###############################################################################

# Create the client connection
host = "localhost"
port = 8086
client = InfluxDBClient(host=host, port=port)

# Connect to the 'weather' database. This must already exist for this to work.
# Using the create_database() function with it already existing will cause this
# script to crash.
dbname = "weather"
client.switch_database(dbname)

###############################################################################
# Anemometer
###############################################################################

CM_IN_A_MILE = 160934.4
SECS_IN_AN_HOUR = 3600
# Calibration factor used to report the correct wind speed
WIND_CALIBRATION = 2.3589722140805094
RADIUS_CM = 9.0  # Radius of the anemometer

wind_speed_sensor = Button(5)  # BCM 5
wind_count = 0  # Number of half rotations for calculating wind speed
store_speeds = []  # Store speeds in order to record wind gusts
store_directions = []  # Store directions to calculate the avg direction


def reset_wind():
    global wind_count
    wind_count = 0


def spin():
    global wind_count
    wind_count = wind_count + 1


def calculate_speed(time_sec):
    logging.log("Calculating the wind speed")
    global wind_count
    circumference_cm = (2 * math.pi) * RADIUS_CM
    rotations = wind_count / 2.0

    # Calculate the distance travelled by a cup in cm
    dist_mile = (circumference_cm * rotations) / CM_IN_A_MILE

    # Report the wind speed in miles per hour
    miles_per_sec = dist_mile / time_sec
    miles_per_hour = miles_per_sec * SECS_IN_AN_HOUR

    # Clear the wind count so it will be ready for the next reading
    reset_wind()

    # The anemometer data sheet indicates that if the switch closes once per
    # second, a wind speed of 1.492 MPH should be reported
    # Multiply by the calibration factor to be accurate according to the
    # data sheet
    return miles_per_hour * WIND_CALIBRATION


# Call the spin function every half rotation
wind_speed_sensor.when_pressed = spin


###############################################################################
# Rain Gauge
###############################################################################

BUCKET_SIZE = 0.011  # Inches per bucket tip

rain_sensor = Button(6)
rain_count = 0
precipitation = 0.0


def bucket_tipped():
    logging.log("Detected a rainfall bucket tip")
    global rain_count
    global precipitation
    rain_count = rain_count + 1
    precipitation = round(rain_count * BUCKET_SIZE, 4)


def reset_rainfall():
    logging.log("Resetting the accumulated rainfall")
    global rain_count
    global precipitation
    rain_count = 0
    precipitation = 0.0


rain_sensor.when_pressed = bucket_tipped


###############################################################################
# Main Program Loop
###############################################################################

# The data file will be named by the current date and time
time_name = datetime.datetime.now().strftime("%m-%d-%Y--%H-%M-%S")
data_file = ""
image_directory = ""
log_file = ""
backup_file = ""
external_storage_connected = False
disk_space_ok = True
previous_day = datetime.datetime.now()
previous_month = datetime.datetime.now()

# Check if an external USB storage device is connected
check_external_drive = subprocess.Popen(
    "df -h | grep /dev/sda1",
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
)
stdout, stderr = check_external_drive.communicate()


# If an external USB storage device is connected, write the data to it
if len(stdout) > 0:
    external_storage_connected = True
    data_file = "/mnt/usb1/" + time_name + ".csv"
    # For some reason, python can't create a subdirectory in the mounted device
    # TODO: Find out if this works
    image_directory = "/mnt/usb1/weather_images" 
    log_file = "/mnt/usb1/" + time_name + ".log"

    # Database location
    database_src = "/var/lib/influxdb/data/" + dbname
    database_dest = "/mnt/usb1/"
# If an external USB storage device isn't connected, write to the repo directory
else:
    data_file = (
        "/home/pi/WeatherStation" + "/" + "data" + "/" + time_name + ".csv"
    )
    image_directory = "/home/pi/WeatherStation/data/weather_images"
    log_file = f"/home/pi/WeatherStation/logs/{time_name}.log"

# Since the PiCamera module seems to not be able to write directly
# to the USB device, they will first be written here, and then copied
# to the drive later.
temp_image_directory = "/home/pi/WeatherStation/data/weather_images"

backup_file = data_file + ".bak"

# Setup the logger. This will create the log_file directory if not already there.
logging.initialize_logger(log_file)

if not external_storage_connected:
    print(
        "WARNING: The data is not being backed up. Ensure an external storage device is connected and restart the system."
    )
    logging.log(
        "WARNING: The data is not being backed up. Ensure an external storage device is connected and restart the system."
    )

print("The weather station has been started")
logging.log("The weather station has been started")
logging.log(f"Readings will be accumulated every {ACCUMULATION_INTERVAL} seconds")
logging.log(f"The data will be written every {LOG_INTERVAL} seconds")
logging.log(f"The data file is located here: {data_file}")

try:
    # Create the data directory if it doesn't already exist
    if not os.path.exists(os.path.dirname(data_file)):
        try:
            os.makedirs(os.path.dirname(data_file))
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    # Create the image directory if it doesn't already exist
    # This needs to be created after the data directory since
    # if the USB drive isn't connected, this directory resides
    # inside the data directory
    try:
        # Note that a trailing slash is required for it to create the last
        # directory specified in the path
        os.makedirs(os.path.dirname(image_directory + "/"), exist_ok=True)
    except OSError as e:
        print(f"ERROR: Could not create {image_directory}")
        logging.log(f"ERROR: Could not create {image_directory}")
        print(str(e))
        raise

    with open(data_file, "w") as file:
        # Write the labels row
        file.write(
            "Record Number,"
            "Time,"
            "Temperature (F),"
            "Pressure (mbars),"
            "Relative Humidity (%),"
            "Wind Direction (Degrees),"
            "Wind Direction (String),"
            "Wind Speed (MPH),"
            "Wind Gust (MPH),"
            "Precipitation (Inches),"
            "Image\n"
        )

    record_number = 1

    ## Database fields
    # The name of the "table" (even though it's not) for the database records
    measurement = "weather"
    location = "backyard"

    ###############################################################################
    # The main program loop
    ###############################################################################
    while True:
        start_time = time.time()

        store_directions = []
        store_speeds = []

        # Accumulate wind direction and wind speeds every ACCUMULATION_INTERVAL
        # seconds, and log the averages every LOG_INTERVAL
        logging.log("Accumulating the sensor readings")
        while time.time() - start_time <= LOG_INTERVAL:

            store_directions.append(wind_direction.get_current_angle())
            store_speeds.append(calculate_speed(ACCUMULATION_INTERVAL))

            time.sleep(ACCUMULATION_INTERVAL)

        # Obtain the wind gust and the average speed over the LOG_INTERVAL
        wind_gust = round(max(store_speeds), 1)
        wind_speed = round(statistics.mean(store_speeds), 1)

        # Obtain the average wind direction over the LOG_INTERVAL
        wind_direction_avg = round(wind_direction.get_average(store_directions), 1)
        wind_direction_string = wind_direction.get_direction_as_string(
            wind_direction_avg
        )

        # Obtain the current humidity, pressure, and ambient temperature
        logging.log(
            "Obtaining the humidity, pressure, and temperature readings from the bme280 sensor"
        )
        try:
            humidity, pressure, ambient_temp = bme280_sensor.read_all()
        except:
            logging.log("ERROR: Attempting to read from the bme280 sensor failed")
            humidity = -1000 # The influx database fails with math.nan
            pressure = -1000
            ambient_temp = -1000

        if shutil.disk_usage(image_directory).free < IMAGE_DISK_USAGE_THRESHOLD:
            disk_space_ok = False
            print(f"Image capturing disabled due to limited remaining disk space: {shutil.disk_usage(image_directory).free} bytes remaining")
            logging.log(f"Image capturing disabled due to limited remaining disk space: {shutil.disk_usage(image_directory).free} bytes remaining")

        # Take a picture of the sky if enabled, if there's enough disk space,
        # and if there is the desired amount of ambient light
        if PHOTOS_ENABLED and disk_space_ok and camera.sufficient_brightness(camera_obj, BRIGHTNESS_THRESHOLD):
            image_name = camera.take_picture(camera_obj, f"{image_directory}")
        else:
            image_name = "nan" # The influx database fails with math.nan

        # This will pull from the Real Time Clock so it can be accurate
        # when there isn't an internet connection. See the readme for
        # instructions on how to configure the Real Time Clock correctly.
        current_time = datetime.datetime.now()

        logging.log("Printing the values obtained and calculated")

        print(f"Record Number:            {record_number}")
        print(f"Time:                     {current_time}")

        # Weather
        print(f"Temperature (F):          {ambient_temp}")
        print(f"Pressure (mbar):          {pressure}")
        print(f"Relative Humidity (%):    {humidity}")
        print(f"Wind Direction (Degrees): {wind_direction_avg}")
        print(f"Wind Direction (String):  {wind_direction_string}")
        print(f"Avg. Wind Speed (MPH):    {wind_speed}")
        print(f"Wind Gust (MPH):          {wind_gust}")
        print(f"Precipitation (Inches):   {precipitation}")
        print(f"Image:                    {image_name}")

        print(
            "##########################################################################"
        )

        logging.log(f"Creating a temporary backup file of the data at {backup_file}")
        backup_data = subprocess.Popen(
            f"cp {data_file} {backup_file}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        stdout, stderr = backup_data.communicate()

        # Log the data by appending the values to the data .csv file
        logging.log(f"Writing the data to {data_file}")
        with open(data_file, "a") as file:
            file.write(
                f"{record_number},{current_time},{ambient_temp},{pressure},"
                f"{humidity},{wind_direction_avg},{wind_direction_string},"
                f"{wind_speed},{wind_gust},{precipitation},{image_name}\n"
            )

        # Write the data to the database as well for Grafana visualization
        logging.log(f"Writing to the database")
        data = [
        {
          "measurement": measurement,
            "tags": {
                "location": location,
            },
            # Use UTC time so it is handled correctly in Grafana
            # Note that this time will be slightly different than
            # the time logged in the CSV. Ideally, I would convert the
            # current_time to utc time.
            "time": datetime.datetime.utcnow(),
            "fields": {
                "Temperature (F)": ambient_temp,
                "Pressure (mbar)": pressure,
                "Relative Humidity (%)": humidity,
                "Wind Direction (Degrees)": wind_direction_avg,
                "Wind Direction (String)": wind_direction_string,
                "Avg. Wind Speed (MPH)": wind_speed,
                "Wind Gust (MPH)": wind_gust,
                "Precipitation (Inches)": precipitation,
                "Image": image_name
            }
        }]
        client.write_points(data)

        # Backup the database
        # WARNING: This will probably limit this to running as root since the
        # database is stored in a root owned directory
        if external_storage_connected:
            logging.log(f"Backing up the database")
            backup_db = subprocess.Popen(
                f"cp -r {database_src} {database_dest}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            stdout, stderr = backup_db.communicate()


        logging.log(f"Removing the temporary backup file {backup_file}")
        remove_temp_backup_file = subprocess.Popen(
            f"rm {backup_file}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        stdout, stderr = remove_temp_backup_file.communicate()

        if not external_storage_connected:
            print(
                "WARNING: The data is not being backed up. Ensure an external storage device is connected and restart the system."
            )
            logging.log(
                "WARNING: The data is not being backed up. Ensure an external storage device is connected and restart the system."
            )

        # Empty the log file every month so it doesn't grow too big
        if int(current_time.strftime("%-m")) != int(previous_month.strftime("%-m")):
            print("Emptying the log file to conserve disk space")
            logging.log("Emptying the log file to conserve disk space")
            clear_log = subprocess.Popen(
                f"rm {log_file}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            stdout, stderr = clear_log.communicate()
            previous_month = current_time

        # Clear the recorded values so they can be updated over the next LOG_INTERVAL
        store_speeds.clear()
        store_directions.clear()

        # Clear the rainfall each day at midnight
        # When it's a new weekday, clear the rainfall total
        if int(current_time.strftime("%w")) != int(previous_day.strftime("%w")):
            print("Resetting the accumulated rainfall")
            reset_rainfall()
            previous_day = current_time

        record_number = record_number + 1

except Exception as e:
    camera_obj.close()
    logging.log("An unhandled exception occurred causing a crash: " + str(e.args))
    traceback.print_exc()
