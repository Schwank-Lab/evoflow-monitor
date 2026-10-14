#!/bin/bash -e
# EvoBridge appliance customisation (pi-gen custom sub-stage, host context).
#   - ${ROOTFS_DIR} : the target rootfs we are populating
#   - on_chroot     : run a command inside that rootfs
#   - files/*       : staged by build-bridge-image.sh (the pico-bridge code)
# CWD is this sub-stage directory, so `files/...` resolves locally.
#
# An EvoBridge connects one EvoFlow reactor (USB serial) to the EvoHub (MQTT over
# the hub's evo-net Wi-Fi): flash the card, plug the reactor in, power on.

# ---------------------------------------------------------------------------
# 1. Bridge code -> /opt/evobridge/pico-bridge. Owned by the login user, because
#    the bridge writes its logs and state files next to the code.
# ---------------------------------------------------------------------------
install -d "${ROOTFS_DIR}/opt/evobridge"
cp -r files/pico-bridge "${ROOTFS_DIR}/opt/evobridge/"
# Which release this bridge runs: cat /opt/evobridge/VERSION
install -m 0644 files/VERSION "${ROOTFS_DIR}/opt/evobridge/VERSION"
on_chroot <<EOF
chown -R ${FIRST_USER_NAME}:${FIRST_USER_NAME} /opt/evobridge
EOF

# ---------------------------------------------------------------------------
# 2. Join the EvoHub's evo-net Wi-Fi. The hub is always at 192.168.4.1 there.
# ---------------------------------------------------------------------------
install -D -m 0600 /dev/stdin \
  "${ROOTFS_DIR}/etc/NetworkManager/system-connections/evo-net.nmconnection" <<'EOF'
[connection]
id=evo-net
type=wifi
interface-name=wlan0
autoconnect=true

[wifi]
mode=infrastructure
ssid=evo-net

[wifi-security]
key-mgmt=wpa-psk
psk=hungryphage

[ipv4]
method=auto

[ipv6]
method=disabled
EOF

# ---------------------------------------------------------------------------
# 3. First boot: a hostname unique to this Pi, and optional overrides from the
#    boot partition (the FAT partition a laptop can open).
# ---------------------------------------------------------------------------
install -D -m 0755 /dev/stdin "${ROOTFS_DIR}/usr/local/sbin/evobridge-firstboot.sh" <<'EOF'
#!/bin/bash
set -e

# The MQTT client id is built from the hostname, and two bridges with the same
# id knock each other off the broker, so each Pi names itself after its serial
# number: evobridge-<last 6 hex digits>.
if [ "$(hostname)" = "evobridge" ]; then
  SERIAL=$(tr -d '\0' < /sys/firmware/devicetree/base/serial-number)
  NAME="evobridge-${SERIAL: -6}"
  raspi-config nonint do_hostname "$NAME"
  hostnamectl set-hostname "$NAME"
  systemctl try-restart avahi-daemon
fi

# Each override file is renamed to *.applied afterwards, so later boots leave
# the configuration alone.
CONF=/boot/firmware/evobridge.conf
if [ -f "$CONF" ]; then
  # shellcheck disable=SC1090
  . "$CONF"
  if [ -n "${COUNTRY:-}" ]; then
    raspi-config nonint do_wifi_country "$COUNTRY"
  fi
  if [ -n "${HUB_SSID:-}" ]; then
    nmcli connection modify evo-net 802-11-wireless.ssid "$HUB_SSID"
  fi
  if [ -n "${HUB_PASSPHRASE:-}" ]; then
    nmcli connection modify evo-net 802-11-wireless-security.psk "$HUB_PASSPHRASE"
  fi
  if [ -n "${MQTT_HOST:-}" ]; then
    sed -i "s/^MQTT_HOST=.*/MQTT_HOST=\"${MQTT_HOST}\"/" /opt/evobridge/pico-bridge/config.py
  fi
  nmcli connection up evo-net || true
  mv "$CONF" "$CONF.applied"
fi

# A public key for SSH login without the default password.
KEYS=/boot/firmware/authorized_keys
if [ -f "$KEYS" ]; then
  install -d -m 0700 -o evobridge -g evobridge /home/evobridge/.ssh
  install -m 0600 -o evobridge -g evobridge "$KEYS" /home/evobridge/.ssh/authorized_keys
  mv "$KEYS" "$KEYS.applied"
fi
EOF

install -D -m 0644 /dev/stdin "${ROOTFS_DIR}/boot/firmware/evobridge.conf.example" <<'EOF'
# Optional EvoBridge overrides. Copy this file to `evobridge.conf` on this
# partition before the bridge's first boot. Every key is optional; leave it
# commented out to keep the default shown.

# Wi-Fi regulatory domain (two-letter country code).
# COUNTRY=CH

# The EvoHub's Wi-Fi network. Change these only if the hub's AP_SSID or
# AP_PASSPHRASE were changed.
# HUB_SSID=evo-net
# HUB_PASSPHRASE=hungryphage

# The EvoHub's MQTT broker.
# MQTT_HOST=192.168.4.1
EOF

# ---------------------------------------------------------------------------
# 4. systemd units
# ---------------------------------------------------------------------------
cat > "${ROOTFS_DIR}/etc/systemd/system/evobridge-firstboot.service" <<'EOF'
[Unit]
Description=EvoBridge unique hostname and overrides from the boot partition
Wants=NetworkManager.service
After=NetworkManager.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/sbin/evobridge-firstboot.sh

[Install]
WantedBy=multi-user.target
EOF

# Restarts every 10 s until the reactor is plugged in and the hub is reachable.
cat > "${ROOTFS_DIR}/etc/systemd/system/evobridge.service" <<EOF
[Unit]
Description=EvoBridge: forward one EvoFlow reactor (USB) to the EvoHub (MQTT)
Wants=network-online.target
After=network-online.target evobridge-firstboot.service

[Service]
User=${FIRST_USER_NAME}
WorkingDirectory=/opt/evobridge/pico-bridge
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

on_chroot <<EOF
systemctl enable evobridge-firstboot.service evobridge.service
EOF
