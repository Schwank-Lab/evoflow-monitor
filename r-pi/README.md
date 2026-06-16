# EvoHub appliance

A pre-configured SD-card image for the EvoHub. Flash it, drop one key file on it,
plug the Pi into ethernet + power, and it boots into a complete, running hub —
**no monitor, no keyboard, no manual setup**.

On boot the hub runs the whole stack (Postgres · Mosquitto · Grafana · MQTT
listener · UI) under `docker compose`, and acts as its **own Wi-Fi access point**
(`evo-net`) for the reactors. It replaces the manual process in the repo-root
`README.md`.

---

# Deploying a hub

For anyone setting up an EvoHub from a finished image. You need: a Raspberry Pi
(4 or 5), an SD card (≥8 GB), an ethernet cable, and the two files below.

## 1. Get the files

- **The image** — `evohub-<date>.img.zip` (from a release, or built by a
  developer; see [For developers](#for-developers)).
- **The deploy key** — a file named `idec_github` (ask the maintainer). The hub
  builds its app images on first boot from the private repo, so it needs this key.

## 2. Flash the image

Use **[Raspberry Pi Imager](https://www.raspberrypi.com/software/)** (Mac /
Windows / Linux):

1. **Choose Device** → skip, or pick your Pi model.
2. **Choose OS** → scroll down → **Use custom** → select the `.img.zip`.
3. **Choose Storage** → select the SD card (it's shown by name/size — so you
   can't pick the wrong disk).
4. **Next** → if asked *"apply OS customisation settings?"* click **No** (the
   image is already configured).
5. Confirm, and enter your computer password when prompted. It writes + verifies.

## 3. Add the deploy key

After flashing, the small `bootfs` partition mounts automatically (macOS:
`/Volumes/bootfs`; Windows: a new drive). Copy the key onto it:

```bash
cp idec_github /Volumes/bootfs/idec_github      # macOS
```

*(Optional)* drop an `evohub.conf` there too, to override the hostname, the AP
name/password, or to use Wi-Fi instead of ethernet — see `evohub.conf.example`
on the partition. Without it, the defaults apply.

Eject the card.

## 4. Boot the Pi

Card into the Pi → **ethernet cable** (required — first boot needs internet) →
**power**. The first boot **builds the app images** (a few minutes), then starts
everything. The `evo-net` Wi-Fi appears once it's up.

## 5. Open the dashboards

Find the hub's IP address on your network (your router's device/DHCP list), then:

- **Grafana** — `http://<hub-ip>:3000`  (login `admin` / `veryhungryphage`)
- **UI** — `http://<hub-ip>:8282`

## 6. Connect reactors

Reactors join the **`evo-net`** Wi-Fi (password `hungryphage`) and talk to the
hub at the fixed address **`192.168.4.1`**. Set this once in the reactor repo's
`pico/configs/default-network_config.json` → `"mqtt_host": "192.168.4.1"`.

## Operating the hub

```bash
ssh evohub@<hub-ip>                 # password: evohub
cd /opt/evohub
docker compose ps                   # are all 5 services Up?
docker compose logs -f listener     # follow a service's logs
```

## If something's off

- **Services not up / first boot slow** — the images are still building. Check
  `systemctl status evohub-build` and `journalctl -u evohub-build`. It needs the
  ethernet/internet and the `idec_github` key from step 3.
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

For building or modifying the appliance image. Design rationale and decisions
are in [`IMAGE_DEPLOYMENT_PLAN.md`](./IMAGE_DEPLOYMENT_PLAN.md).

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

## Build the image

On any machine with **Docker** (~10 GB free, ~20–40 min):

```bash
cd r-pi
./build-image.sh          # output: image/.pi-gen/deploy/*.zip
```

It clones pi-gen, stages the compose/config/source into a custom stage, and runs
the build. **It uses pi-gen's `arm64` branch** — important on Apple Silicon: the
default (32-bit) branch fails on Docker Desktop (`setarch linux32` isn't
supported by its VM kernel), whereas arm64 builds **natively** and skips that
path. Apple Silicon needs no emulation; a Linux x86 host or CI works too.

## How the appliance is assembled

`image/stage-evohub/00-evohub/01-run.sh` bakes into the rootfs:

- **Docker** (official apt repo, codename detected dynamically) + compose plugin.
- **Log rotation** (`/etc/docker/daemon.json`, 50 MB ×3) — the SD card once filled
  with 15 GB of logs and broke Grafana.
- **The `evo-net` AP** — `hostapd` + `dnsmasq` + a static `wlan0` at
  `192.168.4.1/24` + NAT to `eth0`.
- **systemd units** — `evohub-firstboot` (optional `evohub.conf` overrides),
  `evohub-build`, `evohub-nat`, `evohub`.

## Container build (on the Pi, no registry)

Per the project decision, the listener/UI images build **on the Pi at first
boot**, not in a registry. `build-image.sh` stages `evohub/{Docker,evoflow_listener,evoflow_ui}`
into `/opt/evohub/src`; `evohub-build.service` runs once and builds
`idec_base` → `evoflow_listener` → `evoflow_ui` (using the boot-partition
`idec_github` key for the private git deps), then `evohub.service` brings the
stack up. This is why each deployed card needs that key file.

## Changing things

- **Service config / defaults** — `docker/evohub.env`, `docker/docker-compose.yml`.
- **AP SSID / IP / passphrase** — the `hostapd.conf` / `dnsmasq` / `dhcpcd`
  blocks in `01-run.sh`.
- **Python base / build deps** — `evohub/Docker/Dockerfile` (currently
  `python:3.12-alpine`).
- **Image name / user / SSH key** — `image/config`.

## Known issues / caveats

- **UI build on Alpine** — `evoflow_ui` pulls `pandas`; compiling it on
  `python:3.12-alpine` can be slow or need extra build deps. If painful, switch
  `idec_base` to `python:3.12-slim` (Debian wheels).
- **AP on newer OS** — Bookworm/Trixie default to NetworkManager; we hand `wlan0`
  to hostapd. The most likely thing to need tuning on real hardware.
- **First boot needs internet** to build the images. Pre-baking them (true
  offline first boot) is a future enhancement.
- **Deploy key on each card** — a consequence of build-on-Pi/no-registry. The
  cleaner paths (local path deps, or a registry) are in the plan, §6.

## See also

- [`IMAGE_DEPLOYMENT_PLAN.md`](./IMAGE_DEPLOYMENT_PLAN.md) — full design + open decisions.
- Repo-root `README.md` — the legacy manual process (kept for reference/recovery).
