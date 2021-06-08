# Camera
#
# This module can be used to take a picture with the PiCamera.
# It will take a picture and save it to the specified location.
#
# Daniel Hornberger
# 2021

import datetime
import math
from picamera import PiCamera


def take_picture(destination_directory):
    """
    Takes a picture using the PiCamera and saves it to the
    destination_directory named by the date.
    The destination_directory must end in a '/' (e.g. "/home/pi/").
    It will saved as a PNG, and return the path to the image as a string.
    """
    try:
        camera = PiCamera()
        now = datetime.datetime.now()
        location = f"{destination_directory}{now.strftime('%Y-%m-%d_%H:%M%S')}"
        camera.capture(location)
        camera.close()
    except:
        location = math.nan

    return location
