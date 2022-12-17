#!/bin/bash

# This script sets up the Raspberry Pi to have the weather station start up
# on boot. It also performs all the necessary hardware configurations.

echo ""
echo "This script must be run as root."
echo ""

echo "Copying startWeatherStation.sh to /etc/init.d and Enabling the weather station to start on boot"
cp startWeatherStation.sh /etc/init.d/
update-rc.d startWeatherStation.sh defaults

echo "Creating /mnt/usb1 as a mount point for an external storage device..."
mkdir -p /mnt/usb1
sudo chown -R pi:pi /mnt/usb1

echo "Modifying the fstab to mount an external USB storage device to /mnt/usb1..."
echo "/dev/sda1 /mnt/usb1 vfat uid=pi,gid=pi,umask=0022,sync,auto,nofail,nosuid,rw,nouser 0 0" >> /etc/fstab

echo "Setting up a default network to which the Pi should attempt to connect if present..."
printf 'network={\n\tssid="Weather"\n\tpsk="weatherStationNetwork"\n\tkey_mgmt=WPA-PSK\n\tpriority=20\n}\n' >> /etc/wpa_supplicant/wpa_supplicant.conf

echo "Configuring the Pi to synchronize with the Real Time Clock..."
# Add the RTC device to the /etc/modules file
echo "rtc-ds3231" >> /etc/modules
# Delete the last line of the file containing 'exit 0'
sed -i '/exit/d' /etc/rc.local
# Place the following at the end of the file followed by exit 0
# This is what will make the hwclock accessible and sync the Pi's time with the
# time reported by the hwclock when the Pi starts.
printf '/bin/bash -c "echo ds3231 0x68 > /sys/class/i2c-adapter/i2c-1/new_device"\n/sbin/hwclock -s\nexit 0' >> /etc/rc.local
echo "Ensure that the Real Time Clock's time is set correctly. This should be performed manually."
echo "It can be done with 'sudo hwclock -w' while the clock is connected and the 'date' command reports the correct time."

# Create the data and logs directory with the proper permissions
mkdir -p /home/pi/WeatherStation/data /home/pi/WeatherStation/logs
chown pi:pi /home/pi/WeatherStation/data /home/pi/WeatherStation/logs

# Enable ssh connections
echo "Enabling ssh"
sudo systemctl enable ssh
sudo systemctl start ssh

# Install and enable Grafana to start at boot
echo "Installing and enabling Grafana to start on boot..."
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
sudo apt update
sudo apt install grafana -y
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
echo "Grafana is accessible at this machine's IP address and port 3000"

# Install and configure an InfluxDB database
echo "Installing, enabling, and configuring an InfluxDB database to start on boot..."
wget -qO- https://repos.influxdata.com/influxdb.key | sudo apt-key add -
# Note: This command is assuming the Buster version of Raspbian
echo "deb https://repos.influxdata.com/debian buster stable" | sudo tee /etc/apt/sources.list.d/influxdb.list
sudo apt update
sudo apt install influxdb -y
sudo systemctl unmask influxdb
sudo systemctl enable influxdb
sudo systemctl start influxdb

# Create the database and configure it for the weather data
influx -execute "CREATE DATABASE weather"

echo ""
echo "The weather station has been installed!"
echo "The Raspberry Pi must be restarted for the weather station to start automatically."
echo ""

