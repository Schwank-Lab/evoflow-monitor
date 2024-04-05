#!/bin/bash

# Check if the user has provided an argument
if [ $# -eq 0 ]; then
    echo "Usage: $0 <username>"
    exit 1
fi

# Define the user under whose home directory the USB drives will be mounted
USER="$1" # Use the first argument as the username

# Backup /etc/fstab
sudo cp /etc/fstab /etc/fstab.backup

# Function to print messages in green and bold
print_green() {
    echo -e "\033[1;32m$1\033[0m"
}

# Identify attached USB devices
for device in /dev/sd[a-z][1-9]; do
    if [ -b "$device" ]; then
        # Get the UUID and filesystem type
        eval "$(blkid -o export $device)"
        mount_point="/home/$USER/data" # Mounting point now under /home/USER

        # Check if the device is already in fstab
        if ! grep -q "UUID=$UUID" /etc/fstab; then
            # Create a mount point directory
            print_green "Creating mount point $mount_point."
            sudo mkdir -p "$mount_point"

            # Change the owner of the mount point directory to the USER
            sudo chown "$USER:$USER" "$mount_point"

            # Add the device to /etc/fstab with user read and write permissions
            print_green "Adding UUID=$UUID to /etc/fstab with user read/write permissions."
            echo "UUID=$UUID $mount_point $TYPE defaults,noatime,uid=$(id -u $USER),gid=$(id -g $USER) 0 2" | sudo tee -a /etc/fstab > /dev/null
        else
            print_green "Device $device (UUID=$UUID) already in /etc/fstab."
        fi
    fi
done

print_green "Operation completed."
