# EvoHub — manual setup (legacy)

> **Superseded by the [`r-pi/` appliance](./README.md)**, which bakes all of this
> into a pre-built SD image. This is the original from-scratch process, kept for
> reference and recovery. Note it predates several current choices (it uses
> Portainer, an external HDD, the SSID `idec_reactor_fleet` on `172.16.0.x`, etc.).

## Basic system design
A machine hosts the monitor centre with: an MQTT broker (Mosquitto), a database
(PostgreSQL), and Grafana. Each reactor publishes data on a schedule, identifying
itself and the experiment; the hub subscribes, receives, and stores the data.

## Raspberry Pi installation
We use Raspberry Pi OS Lite as the base OS and install Docker on it, with
[Portainer](https://www.portainer.io/) to manage images and containers.

### Installation
Burn Raspberry Pi OS Lite onto the SD card. On first boot the Pi has to be
connected to a display and keyboard to set up the default user and enable ssh.
Then SSH in and run:

```bash
sudo apt install git
mkdir ~/.ssh && cd ~/.ssh && ssh-keygen -t ed25519 -f idec_github
```

In `~/.ssh`, create `config`:
```
Host *.github.com
    AddKeysToAgent yes
    IdentityFile ~/.ssh/idec_github
```

```bash
eval `ssh-agent -s`
ssh-add ~/.ssh/idec_github
git clone git@github.com:Schwank-Lab/evoflow-monitor.git && cd evoflow-monitor/r-pi
sudo chmod +x installme.sh && ./installme.sh   # reboots when done
```

Mount the external HDD (PostgreSQL expects it on `~/data`):
```bash
sudo chmod +x mount_usb_drive.sh
./mount_usb_drive.sh $(whoami)
sudo systemctl daemon-reload && sudo mount -a
mkdir -p ~/data/{postgres,mosquitto/config,mosquitto/data,mosquitto/log,grafana,portainer}
```

#### Portainer
```bash
docker run -d -p 8000:8000 -p 9443:9443 --name portainer --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/home/$USER/data/portainer \
  portainer/portainer-ce:latest
```
Create the admin user via the UI on `:9443`, then upload and deploy the stack file.

#### Mosquitto users
```bash
docker exec -it <container-id> sh
mosquitto_passwd -c /mosquitto/config/pwfile user1   # -c creates; omit to add more
```

## Wi-Fi access point (turn the Pi into a router)
Install prerequisites and configure `hostapd` + `dnsmasq`:
```bash
sudo apt install -y hostapd dnsmasq
sudo DEBIAN_FRONTEND=noninteractive apt install -y netfilter-persistent iptables-persistent
```
Append to `/etc/dhcpcd.conf`:
```
interface wlan0
    static ip_address=172.16.0.1/12
    nohook wpa_supplicant
```
Enable IPv4 routing in `/etc/sysctl.d/routed-ap.conf` (`net.ipv4.ip_forward=1`), add NAT,
and save:
```bash
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
sudo netfilter-persistent save
```
`/etc/dnsmasq.conf`:
```
interface=wlan0
dhcp-range=172.16.0.2,172.16.0.100,255.255.255.0,24h
domain=wlan
address=/gw.wlan/172.16.0.1
```
`/etc/hostapd/hostapd.conf`:
```
country_code=CH
interface=wlan0
ssid=idec_reactor_fleet
hw_mode=g
channel=7
wpa=2
wpa_passphrase=cicciociccio
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```
```bash
sudo rfkill unblock wlan
sudo systemctl unmask hostapd && sudo systemctl enable hostapd && sudo systemctl start hostapd
```

## Docker installation (reference)
The install script handles this; documented for completeness:
```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
```

## References
- [Turn your Raspberry Pi into a Wi-Fi router](https://vaibhavji.medium.com/turn-your-raspberrypi-into-a-wifi-router-5ade510601de)
- [MQTT and compose](https://github.com/sukesh-ak/setup-mosquitto-with-docker)
