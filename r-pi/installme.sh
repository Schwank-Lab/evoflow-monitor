#!/bin/bash

print_green() {
    echo -e "\033[1;32m$1\033[0m"
}

dependencies=(
    "vim"
    "tmux"
    "git"
    "curl"
    "wget"
    "make"
)

# Update and Upgrade
print_green "Updating and upgrading system packages..."
sudo apt update && sudo apt upgrade -y

# Install necessary packages to allow apt to use a repository over HTTPS and other dependencies
print_green "Installing dependencies..."
for package in "${dependencies[@]}"; do
    echo "Installing $package..."
    sudo apt install "$package" -y
done

# Install necessary packages to allow apt to use a repository over HTTPS:
print_green "Installing dependencies for Docker installation..."
sudo apt install apt-transport-https ca-certificates curl gnupg lsb-release -y

# Add Docker’s official GPG key:
print_green "Adding Docker's official GPG key..."
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up the stable repository:
print_green "Setting up the Docker stable repository..."
print_green \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update the apt package index again:
print_green "Updating apt package index..."
sudo apt update

# Install the latest version of Docker Engine and containerd:
print_green "Installing Docker Engine and containerd..."
sudo apt install docker-ce docker-ce-cli -y

sudo usermod -aG docker $USER
# Note: After adding the user to the Docker group, you would need to log out and back in for this to take effect.

print_green "Docker installation complete!"

print_green "Installing Portainer (it will run on port 8000 and 9443)..."
docker run -d -p 8000:8000 -p 9443:9443 --name portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer-ce:latest 

print_green "Making sure SSH agent runs on startup..."
# Define the snippet to add to .bashrc
snippet="if [ -z \"\$SSH_AUTH_SOCK\" ] ; then
  eval \`ssh-agent -s\`
  ssh-add
fi"

# Check if the snippet is already in .bashrc
if grep -qF -- "$snippet" ~/.bashrc; then
  echo "SSH agent snippet is already in .bashrc"
else
  echo "Adding SSH agent snippet to .bashrc..."
  # Append the snippet to .bashrc
  echo "$snippet" >> ~/.bashrc
  echo "Snippet added successfully."
fi

print_green "Installation complete!"

# Countdown before rebooting
print_green "System will reboot in 10 seconds. Press Ctrl+C to cancel."
for i in {10..1..-1}; do
    echo -ne "$i\033[0K\r"
    sleep 1
done

sudo reboot
