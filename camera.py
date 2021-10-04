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
from io import BytesIO
from PIL import Image
from PIL import ImageStat

import logger as logging

def take_picture(destination_directory):
    """
    Takes a picture using the PiCamera and saves it to the
    destination_directory named by the date as a jpeg.
    Do not trail the destination_directory with a '/'. It will be added automatically.
    The image name as a string will be return.
    """
    try:
        # When the camera goes out of scope, camer.close() will automatically be called
        with PiCamera() as camera:
            camera.resolution = (1024, 1024)
            camera.brightness = 50
            now = datetime.datetime.now()
            # Note that camera.capture fails with ':' characters in the filename
            image_name = f"{now.strftime('%Y-%m-%d_%H-%M-%S')}.jpeg"
            camera.capture(destination_directory + "/" + image_name)

    except Exception as e:
        print(f"Exception from camera.py: {str(e.args)}")
        logging.log(f"Exception from camera.py: {str(e.args)}")
        image_name = "nan" # The influx database fails with math.nan

    return image_name



def sufficient_brightness(threshold):
    """
    Determines if the ambient light is sufficient for taking a
    picture with desired level of discernible features as defined
    by the threshold value.
    Valid threshold values are between 0 (black) and 255 (white).
    """
    # Capture an in-memory stream
    stream = BytesIO()
    with PiCamera() as camera:
        camera.capture(stream, format='jpeg')
    # Rewind the stream to the beginning to read its content
    stream.seek(0)
    image = Image.open(stream)

    # https://stackoverflow.com/questions/3490727/what-are-some-methods-to-analyze-image-brightness-using-python#answer-3498247
    stat = ImageStat.Stat(image)
    perceived_brightness = stat.mean[0] 
    logging.log(f"Calculated image brightness: {perceived_brightness}")
    print(f"Calculated image brightness: {perceived_brightness}")

    return perceived_brightness > threshold
