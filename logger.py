# Logger
#
# This file provides a function for logging messages while the weather and
# EMF sensing station is running.

import datetime
import os

log_file = ""


def initialize_logger(log_file_location):
    """
    Create a log file with a timestamp as the name.
    """
    global log_file

    # Create a new file named by the current date and time
    log_file = log_file_location

    # Create the logs directory and log file if they don't already exist
    if not os.path.exists(os.path.dirname(log_file)):
        try:
            os.makedirs(os.path.dirname(log_file))
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise


def log(message):
    """
    Write a log message to the previously created log file.
    """
    global log_file

    time = datetime.datetime.now().strftime("%m-%d-%Y--%H-%M-%S")

    # Append a message to the log file
    with open(log_file, "a") as file:
        file.write(time + " -- " + message + "\n")
