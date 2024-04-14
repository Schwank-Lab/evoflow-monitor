# Monitor
EvoFlow Monitor is the monitor centre for the EvoFlow fleet.

## Responsibilities
EvoFlow Monitor centre will be responsible for:
1. Collect data about experiments 
2. Store data into DB 
3. Show info about the experiments status in a Grafana dashboard

## Basic System design
A machine will host the monitor centre with the following services:
1. MQTT Broker (Mosquito) 
2. A DB (PostgresSQL)
3. Grafana

Each reactor in the fleet publishes data on a schedule (say every 5m) identifying itself an the experiment. The monitor centre subscribes to the topics, receives and stores 
the data in the DB accordingly. 

Furthermore, each reactor will have its own cached data (say 1 day worth of data) that will be published (on a different topic) and analyzed by the control centre for missing data and history integrity. 

## Raspberry PI installation
We use [Raspberry Pi OS Lite](https://wiki.alpinelinux.org/wiki/Raspberry_Pi) as base OS for the Raspberry Pi and install docker system on it. Furthermore, we use [PortainerIO](https://www.portainer.io/) to handle images and containers. 

### Installation
To install a new Raspberry Pi you must download Raspberry Pi OS Lite and burn it into the SD card. Since the newever versions of Raspberry Pi OS, a default user is not longer provided. This means that on first boot the 
Pi has to be connected to a display and a keyboard to set up the default user and enable ssh. Once this is done SSH into the machine and run:

```bash
sudo apt install git
```
Generate an ssh key to add to your GitHub account so that you can clone the repo

```bash
mkdir ~/.ssh && cd ~/.ssh && ssh-keygen -t ed25519 -f idec_github
```

Still in ```~/.ssh``` create a file called ```config``` and paste the following content:
```bash
Host *.github.com
    AddKeysToAgent yes
    IdentityFile ~/.ssh/idec_github
```

Finally, add the key to ssh-agent
```bash
  eval \`ssh-agent -s\`
  ssh-add ~/.ssh/idec_github
```

Add the public key to your GitHub account and clone the repo and cd into the r-pi directory
```bash
git clone https://github.com/Schwank-Lab/evoflow-monitor.git && cd  evoflow-monitor/r-pi
```

Run the installation script 
```bash
./installme.sh
```

PostgresSql is expecting an external hard drive mounted on ```~/data```. Attach an USB HD and run the automount script:
```bash
./mount_usb_hd.sh $(whoami)
sudo systemctl daemon-reload
sudo mount -a
```

We need some directories on the external HD to handle the different volumes for docker, thus on ```~/data```: 
```bash
mkdir -p ~/data/postgres && mkdir -p ~/data/mosquitto/config && mkdir -p ~/data/mosquitto/data && mkdir -p ~/data/mosquitto/log && mkdir -p ~/data/grafana && mkdir -p ~/data/portainer
```

### Docker Installation
Set up Docker's ```apt``` repository.

```bash
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
```

Install the Docker's package

```bash
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```
Add user to docker group (this will avoid using sudo to run docker commands):

1. Create docker group (albeit it should be already there)

```bash
sudo groupadd docker
```

2. Add user to group

```bash
sudo usermod -aG docker $USER
```

Verify installation (should run without sudo)

```bash
docker run hello-world
```

#### Portainer Installation
Once Docker is installd, we use Portainer as UI to handle docker. Let's install it
```bash
docker run -d -p 8000:8000 -p 9443:9443 --name portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:~/data/portainer portainer/portainer-ce:latest 
```
since it's a first installation Portainer will ask to create an admin user and password. Let's do it: connect to the UI running on port 9443 via https.

Once the admin user is created we can upload the stack file (it's a Portainer version of docker-compose), give it a name and click deploy.

#### Mosquitto (mqtt broker)
As at this installation version mqtt config file is locate on ```/var/lib/docker/volumes/monitor_stack_mosquitto/_data/mosquitto.conf``` and the password file in ```/var/lib/docker/volumes/monitor_stack_mosquitto/_data/pwfile```. This is because, despite several attemtps I didn't manage to have change the default location that portainer gives to its volumes.

To create a user/password in the pwfile: 

```bash
# login interactively into the mqtt container
docker exec -it <container-id> sh

# Create new password file and add user and it will prompt for password
mosquitto_passwd -c /mosquitto/config/pwfile user1

# Add additional users (remove the -c option) and it will prompt for password
mosquitto_passwd /mosquitto/config/pwfile user2

# delete user command format
mosquitto_passwd -D /mosquitto/config/pwfile <user-name-to-delete>

# type 'exit' to exit out of docker container prompt

```
Command line help for ```mosquitto_passwd``` command above

```bash
mosquitto_passwd is a tool for managing password files for mosquitto.

Usage: mosquitto_passwd [-H sha512 | -H sha512-pbkdf2] [-c | -D] passwordfile username
       mosquitto_passwd [-H sha512 | -H sha512-pbkdf2] [-c] -b passwordfile username password
       mosquitto_passwd -U passwordfile
 -b : run in batch mode to allow passing passwords on the command line.
 -c : create a new password file. This will overwrite existing files.
 -D : delete the username rather than adding/updating its password.
 -H : specify the hashing algorithm. Defaults to sha512-pbkdf2, which is recommended.
      Mosquitto 1.6 and earlier defaulted to sha512.
 -U : update a plain text password file to use hashed passwords
```

## Set up Wifi Access point. 
I am following [this](https://vaibhavji.medium.com/turn-your-raspberrypi-into-a-wifi-router-5ade510601de). 

***Install prerequisites***

```bash
sudo apt update && sudo apt upgrade

sudo apt install -y hostapd dnsmasq

sudo DEBIAN_FRONTEND=noninteractive apt install -y netfilter-persistent iptables-persistent
```
Reboot the system ```sudo reboot -h now```.

Once the system has reboot let's append the following to the file ```/etc/dhcpcd.conf```

```bash
interface wlan0
    static ip_address=10.10.10.1/24
    nohook wpa_supplicant
```

***Enabling ip4 routing*** by appending the following to the file ```/etc/sysctl.d/routed-ap.conf```

```bash
# Enable IPv4 routing
net.ipv4.ip_forward=1
```

***Setting up firewall rules and save them***

```bash
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

sudo netfilter-persistent save
```

***Setting up dhcp server*** by copying and modifying the default configuration file

```bash
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
```

Modify the configuration file  ```//etc/dnsmasq.conf ```

```bash
interface=wlan0
dhcp-range=10.10.10.2,10.10.10.20,255.255.255.0,24h
domain=wlan
address=/gw.wlan/10.10.10.1
```

Make sure the radio is not blocked

```bash
sudo rfkill unblock wlan
```

***Configuring AP*** by modifying the file in ```/etc/hostapd/hostapd.conf``` as per below

```bash
country_code=CH
interface=wlan0
ssid=idec_reactor_fleet
hw_mode=g
channel=7
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=cicciociccio
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```

Reboot and all should be up and running ```sudo systemctl reboot -h now```.





## Micro-service orchestaration
We use [prefect](https://www.prefect.io/) to handle our workflow. The idea is to have tasks (e.g. create tables in db, insert data, ...) and flows that runs a bunch of tasks on demand. 

# TODO:
- [x] Write docker files for:
    - [x] Mosquito (mqtt broker)
    - [x] PostgresSQL (DB storing data and info about experiments and fleet)
    - [x] Grafana (dashboard)
- [x] Install raspberry pi 
- [ ] Tests:
    - [x] mqtt comms
    - [ ] remove anonymus log-in in mosquitto
    - [ ] data storing
    - [ ] data retrieval
    - [ ] Grafana
- Fixes:
    - [ ] volume location for mqqt


# References:
Some useful links:
- [rabitMQ and Prefect](https://medium.com/civicdatalab/data-orchestration-using-prefect-and-rabbitmq-6349096daca5)
- [Mqtt and compose](https://github.com/sukesh-ak/setup-mosquitto-with-docker)
