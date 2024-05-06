#!/bin/bash

print_green() {
    echo -e "\033[1;32m$1\033[0m"
}

print_red() {
  echo -e "\033[0;31m$@\033[0m"
}

dependencies=(
    "vim"
    "tmux"
    "git"
    "curl"
    "wget"
    "make"
    "pipx"
    "libpq-dev"
    "gcc"
    "dhcpcd5"
)

# Update and Upgrade
print_green "Updating and upgrading system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# Install necessary packages to allow apt to use a repository over HTTPS and other dependencies
print_green "Installing dependencies..."
for package in "${dependencies[@]}"; do
    echo "Installing $package..."
    sudo apt-get install "$package" -y
done

# Install necessary packages to allow apt to use a repository over HTTPS:
print_green "Installing dependencies for Docker installation..."
sudo apt-get install apt-transport-https ca-certificates curl gnupg lsb-release -y

# Add Docker’s official GPG key:
print_green "Adding Docker's official GPG key..."
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Set up the stable repository:
print_green "Setting up the Docker stable repository..."
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update the apt package index again:
print_green "Updating apt package index..."
sudo apt-get update

# Install the latest version of Docker Engine and containerd:
print_green "Installing Docker Engine and containerd..."
sudo apt-get install -y docker  docker-compose

sudo usermod -aG docker $USER
# Note: After adding the user to the Docker group, you would need to log out and back in for this to take effect.

print_green "Docker installation complete!"

print_green "Making sure SSH agent runs on startup..."
# Define the snippet to add to .bashrc
eval \`ssh-agent -s\` >& /dev/null
ssh-add ~/.ssh/idec_github >& /dev/null 

print_green "Adding SSH agent snippet to .bashrc..."
# Append the snippet to .bashrc
echo "$snippet" >> ~/.bashrc
echo "Snippet added successfully."

print_green "Installing Poetry ..."
pipx install poetry

print_green "Installation complete!"

# Countdown before rebooting
print_green "System will reboot in 10 seconds. Press Ctrl+C to cancel."
for i in {10..1..-1}; do
    echo -ne "$i\033[0K\r"
    sleep 1
done

print_red "I am rebooting for the changes to take effect."
sudo reboot -h now
