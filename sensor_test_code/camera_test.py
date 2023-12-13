from picamera import PiCamera
import sys
sys.path.append('../') # trickery to get the path for this simple test
import camera

camera_obj = PiCamera()
camera_obj.resolution = (1024, 1024)
camera_obj.brightness = 50
camera_obj.rotation = 90 

#image_name = camera.take_picture(camera_obj, "/home/pi/WeatherStation/sensor_test_code/")
image_name = camera.take_picture(camera_obj, "/mnt/usb1/weather_images/")
