# EvoHub on Raspberry Pi (appliance)

This is one **deployment** of EvoHub — packaged as a self-contained Raspberry Pi
appliance. Flash a pre-built SD image, plug the Pi into ethernet + power, and it
boots into the complete hub and runs as the reactor fleet's Wi-Fi access point
(`evo-net`). No monitor, no keyboard, no manual setup.

> For **what EvoHub is and how it works** (components, message flow, data model),
> see the [top-level README](../README.md). This page is just how to run it on a Pi.

---

# Deploying a hub

For anyone setting up an EvoHub. You need a Raspberry Pi (4 or 5), an SD card
(≥8 GB), and an ethernet cable.

## 1. Download the image

Grab the latest `evohub-<date>.img.zip` from the repo's
**[Releases](https://github.com/Schwank-Lab/evoflow-monitor/releases)**. That's
the only file you need — all the config is already baked in.

## 2. Flash the image (command line)

Find the SD card, then write the image. **macOS:**

```bash
diskutil list external physical              # find the card → note its diskN (e.g. disk7)
diskutil unmountDisk /dev/diskN
unzip -p evohub-*.img.zip | sudo dd of=/dev/rdiskN bs=4m    # Ctrl-T shows progress
```

**Linux:**
```bash
lsblk                                         # find the card → /dev/sdX
unzip -p evohub-*.img.zip | sudo dd of=/dev/sdX bs=4M status=progress conv=fsync
```

⚠️ Double-check the device — `dd` to the wrong disk wipes it. (If you'd rather not
risk it, the **Raspberry Pi Imager** GUI lists the card by name and works too.)

## 3. (Optional) override defaults

The image works as-is — skip this unless you want to change something. Before
first boot, mount the `bootfs` partition (macOS: `/Volumes/bootfs`) and drop an
**`evohub.conf`** on it to override the hostname, AP name/password, or to use a
Wi-Fi uplink instead of ethernet (see `evohub.conf.example` on the partition).

SSH uses a **password login** — user `evohub`, password `evohub`. Change it after
first boot.

## 4. Boot the Pi

Card into the Pi → **ethernet cable** (the first boot builds the app images and
needs internet) → **power**. The first boot takes a few minutes to build, then
starts everything; the `evo-net` Wi-Fi appears once it's up.

## 5. Open the dashboards

Find the hub's IP on your network (try `ssh evohub@evohub.local`, or your router's
device list), then:

- **Grafana** — `http://<hub-ip>:3000`  (login `admin` / `veryhungryphage`)
- **UI** — `http://<hub-ip>:8282`

## 6. Connect reactors

Reactors join the **`evo-net`** Wi-Fi (password `hungryphage`) and reach the hub
at the fixed address **`192.168.4.1`**. Set this once in the reactor repo's
`pico/configs/default-network_config.json` → `"mqtt_host": "192.168.4.1"`.

## Operating the hub

```bash
ssh evohub@<hub-ip>                 # password: evohub
cd /opt/evohub
docker compose ps                   # are all 5 services Up?
docker compose logs -f listener     # follow a service's logs
```

## If something's off

- **Services not up / first boot slow** — images are still building. Check
  `systemctl status evohub-build` and `journalctl -u evohub-build`. It needs the
  ethernet/internet.
- **No `evo-net` Wi-Fi** — the AP may need tuning on this OS version, but the
  dashboards are still reachable over ethernet, so it won't block you.

## Network reference

| Who talks | To what address |
|---|---|
| hub's own containers (listener/UI → Postgres/Mosquitto) | compose service names (`postgres`, `mosquitto`) |
| reactors → broker | the fixed AP gateway `192.168.4.1` |
| you → Grafana / UI | the hub's IP on your network (DHCP — look it up) |

---

# For developers

For building or modifying the appliance image. Design rationale and open
decisions are in [`IMAGE_DEPLOYMENT_PLAN.md`](./IMAGE_DEPLOYMENT_PLAN.md).

## Layout

```
r-pi/
  build-image.sh          # builds the image (pi-gen in Docker)
  docker/
    docker-compose.yml    # merged backend + apps stack (also usable standalone)
    evohub.env            # baked public defaults
  image/
    config                # pi-gen config (image name, hostname, user, ssh)
    stage-evohub/         # pi-gen custom stage that bakes everything in
```

## Build the image locally

On any machine with **Docker** (~10 GB free, ~20–40 min):

```bash
cd r-pi
./build-image.sh    # output: image/.pi-gen/deploy/*.zip
```

It uses pi-gen's **`arm64` branch** — important on Apple Silicon: the default
(32-bit) branch fails on Docker Desktop (`setarch linux32` isn't supported by its
VM kernel), whereas arm64 builds **natively**. A Linux x86 host or CI works too
(via qemu).

## Publishing a downloadable image (GitHub Releases)

`.github/workflows/build-image.yml` builds the image in CI and attaches the
`.img.zip` to a GitHub Release, so deployers can just download it (§1). Push a
tag like `image-v1` (or run the workflow manually) — it builds and creates a
Release with the image attached.

The image (~900 MB) is well under GitHub's 2 GB release-asset limit.

## How the appliance is assembled

`image/stage-evohub/00-evohub/01-run.sh` bakes into the rootfs: Docker (official
repo), log rotation (`daemon.json`), the **`evo-net` AP** (`hostapd` + `dnsmasq` +
static `wlan0` `192.168.4.1/24` + NAT), and the systemd
units (`evohub-firstboot`, `evohub-build`, `evohub-nat`, `evohub`).

**Container build (on the Pi, no registry):** `build-image.sh` stages
`evohub/{evoflow_listener,evoflow_ui}` into `/opt/evohub/src`;
`evohub-build.service` runs once and builds `evoflow_listener` and `evoflow_ui`
(fetching their `evoflow_db`/`evoflow_utils` dependencies from this repository
over HTTPS), then `evohub.service` brings the stack up.

## Changing things

- **Service config / defaults** — `docker/evohub.env`, `docker/docker-compose.yml`.
- **AP SSID / IP / passphrase** — the `hostapd`/`dnsmasq`/`dhcpcd` blocks in `01-run.sh`.
- **Python base / build deps** — the `Dockerfile`s in `evohub/evoflow_listener` and
  `evohub/evoflow_ui` (`python:3.12-alpine`).
- **Image name / default user / SSH** — `image/config`.

## Known issues / caveats

- **UI build on Alpine** — `evoflow_ui` pulls `pandas`; compiling on
  `python:3.12-alpine` can be slow. If painful, switch both Dockerfiles
  to `python:3.12-slim` (Debian wheels).
- **AP on newer OS** — Bookworm/Trixie default to NetworkManager; we hand `wlan0`
  to hostapd. The most likely thing to need tuning on real hardware.
- **First boot needs internet** to build the images.

## See also

- [`IMAGE_DEPLOYMENT_PLAN.md`](./IMAGE_DEPLOYMENT_PLAN.md) — full design + decisions.
- [`legacy-manual-setup.md`](./legacy-manual-setup.md) — the pre-appliance manual process.
