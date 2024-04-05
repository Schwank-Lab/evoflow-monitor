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
./mount_usb_hd.sh
```

We need some directories on the external HD to handle the different volumes for docker, thus on ```~/data```: 
```bash
mkdir -p ~/data/postgres && mkdir -p ~/data/mosquitto && mkdir -p ~/data/grafana && mkdir -p ~/data/portainer
```

### Docker Installation
We use Portainer as UI to handle docker. Let's install it
```bash
docker run -d -p 8000:8000 -p 9443:9443 --name portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:~/data/portainer portainer/portainer-ce:latest 
```
since it's a first installation Portainer will ask to create an admin user and password. Let's do it: connect to the UI running on port 9443 via https.

Once the admin user is created we can upload the stack file (it's a Portainer version of docker-compose), however before doing that we'll have to make our Mosquitto docker file available:

```bash
cp -R ~/evoflow-monitor/r-pi/docker/mosquitto ~/data/portainer
```



# TODO:
- [ ] Write docker files for:
    - [ ] Mosquito (mqtt broker)
    - [ ] PostgresSQL (DB storing data and info about experiments and fleet)
    - [ ] Grafana (dashboard)
- [ ] Install raspberry pi 
- [ ] Tests:
    - [ ] mqtt comms
    - [ ] data storing
    - [ ] data retrieval
    - [ ] Grafana
