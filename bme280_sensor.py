# Diymore BME280 Humidity, Pressure, and Temperature Sensor Module
#
# Reports the Relative Humidity as a percentage.
# Reports the Barometric Pressure in millibars calibrated to an elevation.
# Reports the Temperature in Fahrenheit or Celsius
#
# Ensure the following connections to the Raspberry Pi 3 Model B:
#
# VIN of the BME280 sensor connected to pin 17 (3v3 Power)
# GND of the BME280 sensor connected to pin 9 (Ground)
# SCL of the BME280 sensor connected to BCM 3 (SCL)
# SDA of the BME280 sensor connected to BCM 2 (SDA)

import bme280
import smbus2
from time import sleep

# Amount to add to the barometer reading for Logan, Utah
# NOTE: This will need to be calibrated for each individual sensor
CALIBRATION = 157.3826

# True will report temperature in F, False will report in C
DO_FAHRENHEIT = True

port = 1
address = 0x76  # BME280 address (Diymore sensor. Adafruit would be 0x77)
bus = smbus2.SMBus(port)

bme280.load_calibration_params(bus, address)

# Samples the BME280 sensor and returns the humidity, temperature, and
# ambient_temperature
def read_all():
    bme280_data = bme280.sample(bus, address)
    humidity = round(bme280_data.humidity, 1)
    pressure = round(bme280_data.pressure + CALIBRATION, 1)
    ambient_temperature = round(bme280_data.temperature, 1)
    if DO_FAHRENHEIT:
        ambient_temperature = round((ambient_temperature * 1.8) + 32, 1)

    return humidity, pressure, ambient_temperature


# This can be used to print the values being read for testing or calibration
# while True:
#    humidity, pressure, ambient_temperature = read_all()
#    print(f"Humidity: {humidity}, Pressure: {pressure}, Temperature: {ambient_temperature}")
#    sleep(1)
