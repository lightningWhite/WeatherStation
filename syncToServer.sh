# This is an rsync command that can be used to backup a directory
# of files to a server. This could be run as a cronjob regularly.
# Each time this command is executed, only the new or changed
# files will be uploaded to the server.
#
# This script expects a file named .env to be present in the
# /home/pi/WeatherStation directory. The contents of this file
# should contain environment variables that specify the server,
# username to login to the server, the local path to backup
# to the server, and the path on the server to where the local
# directory contents should be uploaded.
# Here is an example structure of the .env file, which is not
# included in the repository for security purposes:
#
# BACKUP_SERVER=<place IP address here>
# BACKUP_USER=<place login username here>
# LOCAL_BACKUP_PATH=<path to local folder to backup>
# REMOTE_BACKUP_PATH=<where on the server to copy the local files>
#
# Additionally, an ssh key should be copied to the server so
# an ssh connection can be made without the use of a password.
# Use ssh-keygen to create a key if one doesn't already exist,
# and use 'ssh-copy-id -i user@serverip' to add the key to the
# server. Be sure to test out the connection.

echo ----
date
. /home/pi/WeatherStation/.env
echo Environment vars:
echo Local backup path: $LOCAL_BACKUP_PATH
echo Remote user: $BACKUP_USER
echo Backup server: $BACKUP_SERVER
echo Remote backup path: $REMOTE_BACKUP_PATH
rsync -avh $LOCAL_BACKUP_PATH $BACKUP_USER@$BACKUP_SERVER:$REMOTE_BACKUP_PATH
date

