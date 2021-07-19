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
import logger as logging


def take_picture(destination_directory):
    """
    Takes a picture using the PiCamera and saves it to the
    destination_directory named by the date as a jpeg.
    Do not trail the destination_directory with a '/'. It will be added automatically.
    The image name as a string will be return.

    NOTE: It appears that the camera module can't write to
          a USB drive. It can't find the directory.
          To save to a drive, save the image in another directory,
          and then later move it to the USB drive.
    """
    try:
        # When the camera goes out of scope, camer.close() will automatically be called
        with PiCamera() as camera:
            camera.resolution = (1024, 1024)
            now = datetime.datetime.now()
            image_name = f"{now.strftime('%Y-%m-%d_%H:%M:%S')}.jpeg"
            camera.capture(destination_directory + "/" + image_name)
    except Exception as e:
        print(f"Exception from camera.py: {str(e.args)}")
        logging.log(f"Exception from camera.py: {str(e.args)}")
        image_name = "nan"

    return image_name
