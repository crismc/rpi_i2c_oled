#!/usr/bin/env bash
# Installs RPI_I2C_OLED
# curl -sSL https://install.rpi_i2c_oled | bash
set -e

E_NOTROOT=87 # Non-root exit error.
REPO = "https://github.com/crismc/rpi_i2c_oled.git"
APP_DIR = "rpi_i2c_oled"
TEMP_PATH = "/tmp/$APP_DIR"
INSTALL_PATH = "/etc/$APP_DIR"
SERVICE_NAME = "oled.service"

## check if is sudoer
if ! $(sudo -l &> /dev/null); then
    echo 'Error: root privileges are needed to run this script'
    exit $E_NOTROOT
fi

echo "Getting rpi_i2c_oled"
git clone $REPO $TEMP_PATH

if [ ! -d $TEMP_PATH ]; then
    echo "Could not clone $REPO to $TEMP_PATH"
    echo "Please check your permissions"
    exit $E_NOTROOT
fi

echo "Moving rpi_i2c_oled to $INSTALL_PATH"
sudo mv $TEMP_PATH $INSTALL_PATH

if [ ! -d $INSTALL_PATH ]; then
    echo "Could not move $TEMP_PATH to $INSTALL_PATH"
    echo "Please check your permissions"
    exit $E_NOTROOT
fi

echo "Removing $TEMP_PATH"
rm -fr $TEMP_PATH

if [ -d $TEMP_PATH ]; then
    echo "Could not remove $TEMP_PATH. You may want to do this manually."
fi

echo "Creating service"
sudo ln -s $INSTALL_PATH/$SERVICE_NAME /etc/systemd/system/$SERVICE_NAME

if [ ! -f /etc/systemd/system/$SERVICE_NAME ]; then
    echo "Could not create service"
    echo "Please check your permissions"
    exit $E_NOTROOT
fi

{
    echo "Reloading services"
    sudo systemctl daemon-reload

    echo "Enable on boot start"
    sudo systemctl enable oled.service

    echo "Starting service..."
    sudo service oled start

    echo "-----------"
    echo "Done"
    echo "-----------"
    echo "Control the service with:"
    echo "  service oled start|stop|restart"
} || {
    echo "Could not add service to systemctl"
    echo "You will have to install the service yourself."
    echo "You can manually run the below to start the oled:"
    echo "  python3 $INSTALL_PATH/display.py"
}