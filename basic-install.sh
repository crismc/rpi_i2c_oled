#!/usr/bin/env bash
# Installs RPI_I2C_OLED
# curl -sSL https://install.rpi_i2c_oled | bash
set -e

E_NOTROOT=87 # Non-root exit error.
REPO="crismc/rpi_i2c_oled"
APP_DIR="rpi_i2c_oled"
TEMP_PATH="/tmp/$APP_DIR"
INSTALL_PATH="/etc/$APP_DIR"
SERVICE_NAME="oled.service"

get_latest_release() {
  curl --silent "https://api.github.com/repos/$1/releases/latest" | # Get latest release from GitHub api
    grep '"tag_name":' |                                            # Get tag line
    sed -E 's/.*"([^"]+)".*/\1/'                                    # Pluck JSON value
}

## check if is sudoer
if ! $(sudo -l &> /dev/null); then
    echo 'Error: root privileges are needed to run this script'
    exit $E_NOTROOT
fi

echo "Installing dependencies"
apt-get install i2c-tools git vim
apt-get install python3-dev python3-smbus python3-pil

echo "Getting latest version"
VERSION=$(get_latest_release $REPO)

if [ ! $VERSION ]; then
    echo "Could not get the latest version of $REPO"
    exit $E_NOTROOT
fi

command -v git >/dev/null 2>&1 ||
{ echo >&2 "Git is not installed. Installing..";
    which apt >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "Apt package manager found"
        apt-get install git -y
    else
        which yum >/dev/null 2>&1
        if [ $? -eq 0 ]; then
            echo "Yum package manager found"
            yum install git -y
        else
            echo "Can't work out your package manager."
            echo "Please install git first before running this installer"
            exit
        fi
    fi
}

echo "Getting rpi_i2c_oled"
git clone -b $VERSION --single-branch --depth 1 https://github.com/$REPO.git $TEMP_PATH

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
