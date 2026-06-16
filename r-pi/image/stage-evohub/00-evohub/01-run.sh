#!/bin/bash -e
# EvoHub appliance customisation (pi-gen custom sub-stage, host context).
#   - ${ROOTFS_DIR}  : the target rootfs we are populating
#   - on_chroot      : run a command inside that rootfs
#   - files/*        : staged by build-image.sh (compose, env, app source)
# CWD is this sub-stage directory, so `files/...` resolves locally.

# ---------------------------------------------------------------------------
# 1. Application stack -> /opt/evohub
# ---------------------------------------------------------------------------
install -d "${ROOTFS_DIR}/opt/evohub/mosquitto/config"
install -m 0644 files/docker-compose.yml "${ROOTFS_DIR}/opt/evohub/docker-compose.yml"
install -m 0644 files/evohub.env         "${ROOTFS_DIR}/opt/evohub/.env"

# App source — listener/UI images are built ON THE PI at first boot (no
# registry). See evohub-build.service below.
install -d "${ROOTFS_DIR}/opt/evohub/src"
cp -r files/src/. "${ROOTFS_DIR}/opt/evohub/src/"

cat > "${ROOTFS_DIR}/opt/evohub/mosquitto/config/mosquitto.conf" <<'EOF'
listener 1883 0.0.0.0
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
log_dest stdout
EOF

# ---------------------------------------------------------------------------
# 2. Docker log rotation — the SD card filled with 15 GB of logs once and broke
#    Grafana (see branch claude/keen-maxwell). Cap it by default.
# ---------------------------------------------------------------------------
install -d "${ROOTFS_DIR}/etc/docker"
cat > "${ROOTFS_DIR}/etc/docker/daemon.json" <<'EOF'
{
  "log-driver": "json-file",
  "log-opts": { "max-size": "50m", "max-file": "3" }
}
EOF

# ---------------------------------------------------------------------------
# 3. Wi-Fi access point on wlan0 (the reactor "local" network).
#    Hub is the gateway/DHCP server at a FIXED 192.168.4.1; reactors point here.
#    NOTE: this is the part most likely to need tuning on real hardware
#    (Bookworm defaults to NetworkManager; we hand wlan0 to hostapd/dhcpcd).
# ---------------------------------------------------------------------------
cat > "${ROOTFS_DIR}/etc/hostapd/hostapd.conf" <<'EOF'
country_code=CH
interface=wlan0
ssid=evo-net
hw_mode=g
channel=7
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=hungryphage
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF
cat > "${ROOTFS_DIR}/etc/default/hostapd" <<'EOF'
DAEMON_CONF="/etc/hostapd/hostapd.conf"
EOF

install -d "${ROOTFS_DIR}/etc/dnsmasq.d"
cat > "${ROOTFS_DIR}/etc/dnsmasq.d/evohub.conf" <<'EOF'
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
domain=wlan
address=/gw.wlan/192.168.4.1
EOF

cat >> "${ROOTFS_DIR}/etc/dhcpcd.conf" <<'EOF'

# EvoHub AP — static IP for wlan0
interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
EOF

# Keep NetworkManager (Bookworm default) from managing the AP interface.
install -d "${ROOTFS_DIR}/etc/NetworkManager/conf.d"
cat > "${ROOTFS_DIR}/etc/NetworkManager/conf.d/99-evohub-wlan0.conf" <<'EOF'
[keyfile]
unmanaged-devices=interface-name:wlan0
EOF

# IPv4 forwarding for NAT (wlan0 clients -> eth0 uplink).
cat > "${ROOTFS_DIR}/etc/sysctl.d/99-evohub-routed-ap.conf" <<'EOF'
net.ipv4.ip_forward=1
EOF

# ---------------------------------------------------------------------------
# 4. Optional first-boot overrides from /boot/firmware/evohub.conf
# ---------------------------------------------------------------------------
install -D -m 0755 /dev/stdin "${ROOTFS_DIR}/usr/local/sbin/evohub-firstboot.sh" <<'EOF'
#!/bin/bash
# Apply optional overrides from the boot partition. No file -> no-op.
set -e
CONF=/boot/firmware/evohub.conf
[ -f "$CONF" ] || exit 0
# shellcheck disable=SC1090
. "$CONF"

[ -n "${HOSTNAME:-}" ]       && hostnamectl set-hostname "$HOSTNAME"
[ -n "${AP_SSID:-}" ]        && sed -i "s/^ssid=.*/ssid=${AP_SSID}/" /etc/hostapd/hostapd.conf
[ -n "${AP_PASSPHRASE:-}" ]  && sed -i "s/^wpa_passphrase=.*/wpa_passphrase=${AP_PASSPHRASE}/" /etc/hostapd/hostapd.conf

# Wi-Fi uplink instead of ethernet — needs a USB Wi-Fi dongle on wlan1.
if [ -n "${UPLINK_WIFI_SSID:-}" ] && [ -n "${UPLINK_WIFI_PASS:-}" ]; then
  nmcli connection add type wifi ifname wlan1 con-name evohub-uplink \
    ssid "$UPLINK_WIFI_SSID" wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$UPLINK_WIFI_PASS" || true
fi
EOF

install -D -m 0644 /dev/stdin "${ROOTFS_DIR}/opt/evohub/evohub.conf.example" <<'EOF'
# Optional EvoHub overrides. Copy to the SD card's boot partition as `evohub.conf`.
# Every key is optional; omit to keep the baked defaults.

# HOSTNAME=evohub
# AP_SSID=evo-net
# AP_PASSPHRASE=hungryphage

# Wi-Fi uplink instead of ethernet (requires a USB Wi-Fi dongle on wlan1):
# UPLINK_WIFI_SSID=MyLabWifi
# UPLINK_WIFI_PASS=secret
EOF

# ---------------------------------------------------------------------------
# 5. Build the app images on the Pi at first boot (no registry).
#    Needs the GitHub key dropped on the boot partition as
#    /boot/firmware/idec_github (so poetry can fetch the private git deps),
#    plus internet. Runs once (guarded by /opt/evohub/.built).
# ---------------------------------------------------------------------------
install -D -m 0755 /dev/stdin "${ROOTFS_DIR}/usr/local/sbin/evohub-build.sh" <<'EOF'
#!/bin/bash
set -e
SRC=/opt/evohub/src
KEY=/boot/firmware/idec_github
if [ ! -f "$KEY" ]; then
  echo "evohub-build: no GitHub key at $KEY — drop it there to build the app images." >&2
  exit 1
fi
docker build --build-arg ssh_private_key="$(cat "$KEY")" -t idec_base "$SRC/Docker"
docker build -t evoflow_listener "$SRC/evoflow_listener"
docker build -t evoflow_ui       "$SRC/evoflow_ui"
touch /opt/evohub/.built
EOF

# ---------------------------------------------------------------------------
# 6. systemd units
# ---------------------------------------------------------------------------
cat > "${ROOTFS_DIR}/etc/systemd/system/evohub-firstboot.service" <<'EOF'
[Unit]
Description=EvoHub first-boot overrides (optional /boot/firmware/evohub.conf)
After=local-fs.target
Before=hostapd.service dnsmasq.service evohub.service
ConditionPathExists=/boot/firmware/evohub.conf

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/sbin/evohub-firstboot.sh

[Install]
WantedBy=multi-user.target
EOF

cat > "${ROOTFS_DIR}/etc/systemd/system/evohub-build.service" <<'EOF'
[Unit]
Description=EvoHub build app images (listener, UI) on the Pi
Requires=docker.service
After=docker.service network-online.target evohub-firstboot.service
Wants=network-online.target
ConditionPathExists=!/opt/evohub/.built

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/sbin/evohub-build.sh

[Install]
WantedBy=multi-user.target
EOF

cat > "${ROOTFS_DIR}/etc/systemd/system/evohub-nat.service" <<'EOF'
[Unit]
Description=EvoHub NAT (wlan0 reactor clients -> eth0 uplink)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/sh -c 'iptables -t nat -C POSTROUTING -o eth0 -j MASQUERADE 2>/dev/null || iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE'

[Install]
WantedBy=multi-user.target
EOF

cat > "${ROOTFS_DIR}/etc/systemd/system/evohub.service" <<'EOF'
[Unit]
Description=EvoHub docker compose stack
Requires=docker.service
After=docker.service network-online.target evohub-build.service
Wants=network-online.target

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

systemctl unmask hostapd
rfkill unblock wlan || true
systemctl enable hostapd dnsmasq docker \
  evohub-firstboot.service evohub-build.service evohub-nat.service evohub.service
EOF
