# Wind Direction
#
# Uses the ADC to read the voltage from the wind direction sensor
# and maps it do the corresponding direction. It then averages the readings
# over a period of time and then logs the average.
#
# Ensure the following connections:
#
# Anemometer connected into the Wind Direction Sensor
# Wind Direction Sensor connected to the RJ11 connector
# Pin 2 on the RJ11 connector to 3v3
# Pin 5 on the RJ11 connector to pin 1 (CH0) on the MCP3208
# Pin 3 on the RJ11 connector to Ground (For the anemometer)
# Pin 4 on the RJ11 connector to BCM 5 (For the anemometer)
# Ground to pin 9 on the MCP3208 chip
# BCM 8 (CE0) to pin 10 (CS/SHDN) on the MCP3208 chip
# BCM 10 (MOSI) to pin 11 (Din) on the MCP3208 chip
# BCM 9 (MISO) to pin 12 (Dout) on the MCP3208 chip
# BCM 11 (SCLK) to pin 13 (CLK) on the MCP3208 chip
# Ground to pin 14 (AGND) on the MCP3208 chip
# 3v3 to pin 15 on (Vref) the MCP3208 chip
# 3v3 to pin 16 on (Vdd) the MCP3208 chip
# 4.7kohm resistor from ground to pin 1 on the MCP3208 chip for voltage div

from gpiozero import MCP3208

import logger as logging
import math
import time

# How often the average wind direction should be logged
LOG_INTERVAL = 5  # 900 # 15 Minutes

# Analog to Digital Converter
adc = MCP3208(channel=0)

# These voltage values mapped to headings came from the Raspberry Pi
# weather station tutorial (see the readme). However, the voltages came
# from an incorrect voltage divider equation.
# In the tutorial, they used the following equation:
# vout = (vin * r1) / (r1 + r2)
# It should have been the following:
# vout = (vin * r2) / (r1 + r2)
# However, with a vin of 3v3 and the external resistor of 4.7kohms
# (r1 in their equation), there are 16 different values, so it works.
# Due to limited resources and time, I left it as they had it rather
# than find a different resistor value that would also work.
volts = {
    0.4: 0.0,
    1.4: 22.5,
    1.2: 45.0,
    2.8: 67.5,
    2.7: 90.0,
    2.9: 112.5,
    2.2: 135.0,
    2.5: 157.5,
    1.8: 180.0,
    2.0: 202.5,
    0.7: 225.0,
    0.8: 247.5,
    0.1: 270.0,
    0.3: 292.5,
    0.2: 315.0,
    0.6: 337.5,
}

# Calculate the average angle from a list of angles
def get_average(angles):
    logging.log("Calculating the average of the list of angles")

    sin_sum = 0.0
    cos_sum = 0.0

    for angle in angles:
        r = math.radians(angle)
        sin_sum += math.sin(r)
        cos_sum += math.cos(r)

    flen = float(len(angles))

    # Don't allow division by 0
    if flen == 0:
        return 0.0

    s = sin_sum / flen
    c = cos_sum / flen
    arc = math.degrees(math.atan(s / c))
    average = 0.0

    if s > 0 and c > 0:
        average = arc
    elif c < 0:
        average = arc + 180
    elif s < 0 and c > 0:
        average = arc + 360

    return 0.0 if average == 360 else average


# Returns the average direction read over a period of time
def get_value(time_period=LOG_INTERVAL):
    global volts

    logging.log("Obtaining the average wind direction over a period of time")

    data = []
    expected_voltages = volts.keys()
    start_time = time.time()

    while time.time() - start_time <= time_period:

        voltage = round(adc.value * 3.3, 3)

        closest_voltage = min(expected_voltages, key=lambda x: abs(x - voltage))
        data.append(volts[closest_voltage])

    return get_average(data)


# Returns the current wind direction
def get_current_angle():
    global volts

    logging.log("Obtaining the current wind direction angle")

    expected_voltages = volts.keys()
    voltage = round(adc.value * 3.3, 3)
    closest_voltage = min(expected_voltages, key=lambda x: abs(x - voltage))

    # Return the angle mapped to the voltage read
    return volts[closest_voltage]


# A map that maps headings to wind direction strings
directions = {
    0.0: "N",
    22.5: "NNE",
    45.0: "NE",
    67.5: "ENE",
    90.0: "E",
    112.5: "ESE",
    135.0: "SE",
    157.5: "SSE",
    180.0: "S",
    202.5: "SSW",
    225.0: "SW",
    247.5: "WSW",
    270.0: "W",
    292.5: "WNW",
    315.0: "NW",
    337.5: "NNW",
}


def get_direction(time_period=LOG_INTERVAL):
    global directions

    value = get_value(time_period)

    expected_directions = directions.keys()
    closest_direction = min(expected_directions, key=lambda x: abs(x - value))

    return directions[closest_direction]


def get_direction_as_string(angle):
    global directions

    logging.log("Converting an angle direction to a string")

    expected_directions = directions.keys()
    closest_direction = min(expected_directions, key=lambda x: abs(x - angle))

    return directions[closest_direction]
