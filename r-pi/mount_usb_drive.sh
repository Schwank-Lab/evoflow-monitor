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

# Identify attached USB devices
for device in /dev/sd[a-z][1-9]; do
    if [ -b "$device" ]; then
        # Get the UUID and filesystem type
        eval "$(blkid -o export $device)"
        mount_point="/home/$USER/data/"

        # Check if the device is already in fstab
        if ! grep -q "UUID=$UUID" /etc/fstab; then
            # Create a mount point directory
            echo "Creating mount point $mount_point."
            sudo mkdir -p "$mount_point"

            # Add the device to /etc/fstab
            echo "Adding UUID=$UUID to /etc/fstab."
            echo "UUID=$UUID $mount_point $TYPE defaults,noatime 0 2" | sudo tee -a /etc/fstab > /dev/null
        else
            echo "Device $device (UUID=$UUID) already in /etc/fstab."
        fi
    fi
done

echo "Operation completed."
