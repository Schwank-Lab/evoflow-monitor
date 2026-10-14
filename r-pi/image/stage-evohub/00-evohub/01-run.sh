#!/bin/bash -e
# EvoHub appliance customisation (pi-gen custom sub-stage, host context).
#   - ${ROOTFS_DIR}  : the target rootfs we are populating
#   - on_chroot      : run a command inside that rootfs
#   - files/*        : staged by build-image.sh (compose, env, Grafana provisioning)
#   - /evohub-images : the container images, mounted in by build-image.sh
# CWD is this sub-stage directory, so `files/...` resolves locally.

# ---------------------------------------------------------------------------
# 1. Application stack -> /opt/evohub
# ---------------------------------------------------------------------------
install -d "${ROOTFS_DIR}/opt/evohub/mosquitto/config"
install -m 0644 files/docker-compose.yml "${ROOTFS_DIR}/opt/evohub/docker-compose.yml"
install -m 0644 files/evohub.env         "${ROOTFS_DIR}/opt/evohub/.env"

# Grafana datasource + dashboards. The compose file mounts these into the
# container, so EvoMonitor is there on first boot rather than an empty Grafana.
install -d "${ROOTFS_DIR}/opt/evohub/grafana"
cp -r files/grafana/. "${ROOTFS_DIR}/opt/evohub/grafana/"

# Every container image the stack uses, loaded into Docker at first boot, so the
# hub never needs internet access.
install -D -m 0644 /evohub-images/evohub-images.tar \
  "${ROOTFS_DIR}/opt/evohub/images/evohub-images.tar"

cat > "${ROOTFS_DIR}/opt/evohub/mosquitto/config/mosquitto.conf" <<'EOF'
listener 1883 0.0.0.0
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
log_dest stdout
EOF

# ---------------------------------------------------------------------------
# 2. Docker log rotation, so container logs cannot fill the SD card.
# ---------------------------------------------------------------------------
install -d "${ROOTFS_DIR}/etc/docker"
cat > "${ROOTFS_DIR}/etc/docker/daemon.json" <<'EOF'
{
  "log-driver": "json-file",
  "log-opts": { "max-size": "50m", "max-file": "3" }
}
EOF

# ---------------------------------------------------------------------------
# 3. evo-net Wi-Fi access point on wlan0.
#    NetworkManager runs the access point, gives the hub the fixed address
#    192.168.4.1, hands out addresses to clients (DHCP) and shares any uplink
#    (ethernet, or Wi-Fi on a USB dongle) with them. EvoBridges and laptops join
#    evo-net and reach the hub at 192.168.4.1. 2.4 GHz (band bg) so that every
#    client can join.
# ---------------------------------------------------------------------------
install -D -m 0600 /dev/stdin \
  "${ROOTFS_DIR}/etc/NetworkManager/system-connections/evo-net.nmconnection" <<'EOF'
[connection]
id=evo-net
type=wifi
interface-name=wlan0
autoconnect=true

[wifi]
mode=ap
ssid=evo-net
band=bg
channel=6

[wifi-security]
key-mgmt=wpa-psk
proto=rsn
pairwise=ccmp
group=ccmp
psk=hungryphage

[ipv4]
method=shared
address1=192.168.4.1/24

[ipv6]
method=disabled
EOF

# ---------------------------------------------------------------------------
# 4. Optional overrides from the boot partition (the FAT partition a laptop can
#    open), applied once at first boot.
# ---------------------------------------------------------------------------
install -D -m 0755 /dev/stdin "${ROOTFS_DIR}/usr/local/sbin/evohub-firstboot.sh" <<'EOF'
#!/bin/bash
# Apply the overrides a deployer put on the boot partition. Each file is renamed
# to *.applied afterwards, so later boots leave the configuration alone.
set -e

CONF=/boot/firmware/evohub.conf
if [ -f "$CONF" ]; then
  # shellcheck disable=SC1090
  . "$CONF"
  if [ -n "${COUNTRY:-}" ]; then
    raspi-config nonint do_wifi_country "$COUNTRY"
  fi
  if [ -n "${HUB_HOSTNAME:-}" ]; then
    raspi-config nonint do_hostname "$HUB_HOSTNAME"
    hostnamectl set-hostname "$HUB_HOSTNAME"
    systemctl try-restart avahi-daemon
  fi
  if [ -n "${AP_SSID:-}" ]; then
    nmcli connection modify evo-net 802-11-wireless.ssid "$AP_SSID"
  fi
  if [ -n "${AP_PASSPHRASE:-}" ]; then
    nmcli connection modify evo-net 802-11-wireless-security.psk "$AP_PASSPHRASE"
  fi
  # Wi-Fi uplink instead of ethernet. Needs a USB Wi-Fi dongle (wlan1), because
  # the on-board radio is busy being the access point.
  if [ -n "${UPLINK_WIFI_SSID:-}" ]; then
    nmcli connection add type wifi ifname wlan1 con-name evohub-uplink \
      ssid "$UPLINK_WIFI_SSID" wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$UPLINK_WIFI_PASS"
  fi
  nmcli connection up evo-net || true
  mv "$CONF" "$CONF.applied"
fi

# A public key for SSH login without the default password.
KEYS=/boot/firmware/authorized_keys
if [ -f "$KEYS" ]; then
  install -d -m 0700 -o evohub -g evohub /home/evohub/.ssh
  install -m 0600 -o evohub -g evohub "$KEYS" /home/evohub/.ssh/authorized_keys
  mv "$KEYS" "$KEYS.applied"
fi
EOF

install -D -m 0644 /dev/stdin "${ROOTFS_DIR}/boot/firmware/evohub.conf.example" <<'EOF'
# Optional EvoHub overrides. Copy this file to `evohub.conf` on this partition
# before the hub's first boot. Every key is optional; leave it commented out to
# keep the default shown.

# Wi-Fi regulatory domain (two-letter country code).
# COUNTRY=CH

# HUB_HOSTNAME=evohub

# The hub's own Wi-Fi network, which EvoBridges and laptops join.
# AP_SSID=evo-net
# AP_PASSPHRASE=hungryphage

# Wi-Fi uplink instead of ethernet (requires a USB Wi-Fi dongle):
# UPLINK_WIFI_SSID=MyLabWifi
# UPLINK_WIFI_PASS=secret
EOF

# ---------------------------------------------------------------------------
# 5. Load the preloaded container images into Docker at first boot.
# ---------------------------------------------------------------------------
install -D -m 0755 /dev/stdin "${ROOTFS_DIR}/usr/local/sbin/evohub-load.sh" <<'EOF'
#!/bin/bash
# Load the container images shipped in the SD image into Docker, then delete the
# tarball to free its space on the card.
set -e
docker load -i /opt/evohub/images/evohub-images.tar
rm /opt/evohub/images/evohub-images.tar
touch /opt/evohub/.loaded
EOF

# ---------------------------------------------------------------------------
# 6. systemd units
# ---------------------------------------------------------------------------
cat > "${ROOTFS_DIR}/etc/systemd/system/evohub-firstboot.service" <<'EOF'
[Unit]
Description=EvoHub overrides from the boot partition (evohub.conf, authorized_keys)
Wants=NetworkManager.service
After=NetworkManager.service
ConditionPathExists=|/boot/firmware/evohub.conf
ConditionPathExists=|/boot/firmware/authorized_keys

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/sbin/evohub-firstboot.sh

[Install]
WantedBy=multi-user.target
EOF

cat > "${ROOTFS_DIR}/etc/systemd/system/evohub-load.service" <<'EOF'
[Unit]
Description=EvoHub load the preloaded container images into Docker
Requires=docker.service
After=docker.service
ConditionPathExists=!/opt/evohub/.loaded

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/sbin/evohub-load.sh

[Install]
WantedBy=multi-user.target
EOF

cat > "${ROOTFS_DIR}/etc/systemd/system/evohub.service" <<'EOF'
[Unit]
Description=EvoHub docker compose stack
Requires=docker.service
Wants=evohub-load.service
After=docker.service evohub-load.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/evohub
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down

[Install]
WantedBy=multi-user.target
EOF

# ---------------------------------------------------------------------------
# 7. Inside the chroot: install Docker (official repo) + enable everything
# ---------------------------------------------------------------------------
on_chroot <<EOF
set -e
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \$(. /etc/os-release && echo \$VERSION_CODENAME) stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
usermod -aG docker ${FIRST_USER_NAME}

systemctl enable docker evohub-firstboot.service evohub-load.service evohub.service
EOF
