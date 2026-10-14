# EvoHub and EvoBridge on Raspberry Pi (appliances)

Two pre-built SD card images:

- **EvoHub** — collects, stores and shows the data of a whole reactor fleet. It
  runs Postgres, the Mosquitto MQTT broker, Grafana (EvoMonitor), the MQTT
  listener and the web UI, and creates its own Wi-Fi network, **`evo-net`**.
- **EvoBridge** — one per reactor. Plugged into an EvoFlow reactor by USB, it
  joins `evo-net` and forwards the reactor's state to the hub, and the hub's
  commands back to the reactor.

Flash, power on, done: no monitor, no keyboard, no internet needed. Both images
come pre-paired — a bridge finds a hub with the default settings by itself.

> For **what EvoHub is and how it works** (components, message flow, data model),
> see the [top-level README](../README.md). This page is how to run it on Pis.

---

# Deploying

You need one Raspberry Pi 5 (or 4) for the hub, one per reactor for the bridges,
and a microSD card (≥16 GB) for each.

## 1. Download the images

From the repo's **[Releases](https://github.com/Schwank-Lab/evoflow-monitor/releases)**:
`evohub-<date>.img.xz` and `evobridge-<date>.img.xz`. Everything is baked in.

## 2. Flash the cards

**Raspberry Pi Imager** (recommended — it lists cards by name): *Choose OS* →
*Use custom* → pick the `.img.xz`; *Choose storage* → the card; *Next*. When asked
**"Would you like to apply OS customisation settings?" choose _No_** — the
images configure themselves, and customisation would switch the hub's Wi-Fi from
access point to client.

Or from the command line (macOS):

```bash
diskutil list external physical              # find the card → note its diskN (e.g. disk7)
diskutil unmountDisk /dev/diskN
xz -dc evohub-*.img.xz | sudo dd of=/dev/rdiskN bs=4m    # Ctrl-T shows progress
```

⚠️ Double-check the device — `dd` to the wrong disk wipes it.

## 3. (Optional) override defaults

The images work as-is. To change something, open the card's boot partition
(macOS: `/Volumes/bootfs`) before the first boot and copy the example file there
to its real name, then edit it:

- hub: `evohub.conf.example` → `evohub.conf` — country, hostname, `evo-net` name
  and password, or a Wi-Fi uplink (needs a USB Wi-Fi dongle).
- bridge: `evobridge.conf.example` → `evobridge.conf` — country, the hub's Wi-Fi
  name and password (if you changed them on the hub), MQTT broker address.

To log in over SSH with a key instead of the default password, also put your
public key on the boot partition as `authorized_keys`.

## 4. Start the hub

Card in → power. Ethernet is optional: connected, the hub shares its internet
with `evo-net` and keeps its clock correct. The first boot loads the container
images (a few minutes); then the **`evo-net`** Wi-Fi appears.

Join `evo-net` (password `hungryphage`) from a laptop and open:

- **Grafana / EvoMonitor** — `http://192.168.4.1:3000` (login `admin` / `veryhungryphage`).
  It opens on the EvoMonitor dashboard, showing the most recently started
  experiment; pick another from the *experiment_name* dropdown.
- **UI** — `http://192.168.4.1:8282`

Over ethernet, the hub is also at `http://evohub.local:3000` (or its IP from the
router's device list).

## 5. Connect the reactors

For each reactor: card into a bridge Pi → reactor's USB into the bridge → power.
The bridge names itself `evobridge-<6 hex digits of its serial number>`, joins
`evo-net` and starts forwarding. Data appears in EvoMonitor once an experiment is
running.

Evotool (on a laptop joined to `evo-net`) reaches the hub's database at
`192.168.4.1` by default — needed for `evotool.py register` and
`evotool.py experiment new`. From the lab network instead, set `DB_HOST` and
`MQTT_HOST` to the hub's address.

## 6. Test without a reactor

[`fake_reactor`](../fake_reactor) registers a simulated reactor and experiment on
the hub and streams turbidostat-like data, so you can check the whole hub before
any hardware is ready. From a laptop on `evo-net`:

```bash
cd fake_reactor && poetry install
poetry run fake-reactor                      # Ctrl+C to stop
```

It is the newest experiment, so EvoMonitor shows it straight away.

## Operating

```bash
ssh evohub@192.168.4.1              # password: evohub (or evohub@evohub.local)
cd /opt/evohub
docker compose ps                   # postgres, mosquitto, grafana, listener, ui Up; db-init Exited (0)
docker compose logs -f listener     # follow a service's logs

ssh evobridge@<bridge>.local        # password: evobridge
systemctl status evobridge          # journalctl -u evobridge -f for its log
```

## If something's off

- **No `evo-net` Wi-Fi** — wait a minute after power-on; check
  `nmcli connection show --active` on the hub (via ethernet).
- **Services not up** — the first boot loads the images: `systemctl status evohub-load`.
- **Dashboard empty although data arrives** — EvoMonitor plots data by the hub's
  clock. A Pi has no battery-backed clock by default, so after a power cut
  without internet its time is wrong. Connect ethernet, fit a Raspberry Pi RTC
  battery, or set the time: `ssh evohub@192.168.4.1 sudo date -s "<now>"`.
- **Bridge not forwarding** — `journalctl -u evobridge -f`; it retries every 10 s
  until the reactor is plugged in and the hub is reachable.

## Network reference

| Who talks | To what address |
|---|---|
| hub's own containers (listener/UI → Postgres/Mosquitto) | compose service names (`postgres`, `mosquitto`) |
| bridges → MQTT broker, Evotool → database | `192.168.4.1` (the hub on `evo-net`) |
| you → Grafana / UI | `192.168.4.1` on `evo-net`; `evohub.local` or the hub's IP on ethernet |

---

# For developers

For building or modifying the images. Design rationale is in
[`IMAGE_DEPLOYMENT_PLAN.md`](./IMAGE_DEPLOYMENT_PLAN.md).

## Layout

```
r-pi/
  build-image.sh          # builds the EvoHub image
  build-bridge-image.sh   # builds the EvoBridge image
  docker/
    docker-compose.yml    # the hub's stack (also usable on any Docker host)
    evohub.env            # baked public defaults
    grafana/              # provisioned datasource + EvoMonitor dashboard
  image/
    config                # pi-gen config, hub
    config-evobridge      # pi-gen config, bridge
    stage-evohub/         # pi-gen custom stage for the hub
    stage-evobridge/      # pi-gen custom stage for the bridge
```

## Build the images locally

On a machine with **Docker 28+** that can run `linux/arm64` containers (Apple
Silicon natively; elsewhere via qemu), ~15 GB free per image, ~20–60 min each:

```bash
cd r-pi
./build-image.sh                                # → image/.pi-gen/deploy/evohub-<date>.img.xz
./build-bridge-image.sh                         # → image/.pi-gen-evobridge/deploy/evobridge-<date>.img.xz
REACTOR_REF=<branch|tag|commit> ./build-bridge-image.sh   # bridge code from another evoflow-reactor ref
```

Both use pi-gen's **`arm64` branch** — on Apple Silicon the default (32-bit)
branch fails on Docker Desktop (`setarch linux32` isn't supported by its VM
kernel), whereas arm64 builds natively.

## Publishing (GitHub Releases)

`.github/workflows/build-image.yml` builds both images on native arm64 runners.
Pull requests that touch the images build them as a check (downloadable from the
run's artifacts); pushing a tag like `image-v1` attaches them, with checksums,
to a GitHub Release.

## How the hub image is assembled

`build-image.sh` builds the listener and UI images and pulls Postgres, Mosquitto
and Grafana (all `linux/arm64`, versions pinned in `docker-compose.yml`), and
saves every image the compose file uses into one tarball. pi-gen then builds
Raspberry Pi OS Lite plus `image/stage-evohub/00-evohub/01-run.sh`, which adds:
Docker (official repo), log rotation, the compose stack in `/opt/evohub`, the
image tarball, the **`evo-net` access point** (one NetworkManager connection:
`192.168.4.1/24`, DHCP and NAT to any uplink), and the systemd units
`evohub-firstboot` (boot-partition overrides), `evohub-load` (`docker load` on
first boot) and `evohub` (`docker compose up`). On start, the `db-init` service
creates the database tables before the listener and UI start.

## How the bridge image is assembled

`build-bridge-image.sh` fetches `pico-bridge/` from evoflow-reactor at
`REACTOR_REF`. pi-gen builds Raspberry Pi OS Lite plus
`image/stage-evobridge/00-evobridge/01-run.sh`, which adds the bridge code in
`/opt/evobridge`, its two Python dependencies from Debian (`python3-serial`,
`python3-paho-mqtt`), a NetworkManager connection that joins `evo-net`, and the
systemd units `evobridge-firstboot` (unique hostname, boot-partition overrides)
and `evobridge` (the bridge itself, restarted until it connects).

## Changing things

- **Service config / defaults** — `docker/evohub.env`, `docker/docker-compose.yml`.
- **Service versions** — the image tags in `docker/docker-compose.yml`.
- **`evo-net` name / password / address** — the `evo-net.nmconnection` blocks in
  both `01-run.sh` files (keep hub and bridge in step).
- **Python base / build deps** — the `Dockerfile`s in `evohub/evoflow_listener`
  and `evohub/evoflow_ui` (`python:3.12-alpine`).
- **Image name / default user / SSH** — `image/config`, `image/config-evobridge`.

## See also

- [`IMAGE_DEPLOYMENT_PLAN.md`](./IMAGE_DEPLOYMENT_PLAN.md) — design and decisions.
- [`legacy-manual-setup.md`](./legacy-manual-setup.md) — the pre-appliance manual process.
