# Influx Backup
#
# This script automates the backup process for the Influx database.
# It rotates a previous and a latest backup to prevent data loss if
# the power goes out during a backup. This can be called by a cronjob.

. /home/pi/WeatherStation/.env
rm -rf $LOCAL_BACKUP_PATH/influxBackupPrev
mv $LOCAL_BACKUP_PATH/influxBackupLatest $LOCAL_BACKUP_PATH/influxBackupPrev
influxd backup -portable $LOCAL_BACKUP_PATH/influxBackupLatest
