# EvoHub Image-Based Deployment — Plan

Status: **draft / proposal (v2)** · Branch: `image-based-deployment`

> v2 changes from v1: dropped Ansible (shell build instead); service configs use
> the existing **public defaults** baked into the image, so credential
> **injection is now optional**, not a core pillar; **hub-as-AP** is the baseline
> topology; **mDNS dropped** (users access by IP, as today). See the changelog at
> the bottom.

## 0. Goal

A non-technical user (a biologist) brings up a complete, working EvoHub with **no
monitor, no keyboard, no copy-paste, and no shell commands** — from a **pre-baked
SD-card image** that boots straight into a running hub.

Key simplification settled during design: because every service uses
**non-sensitive public defaults** (there is no sensitive data anywhere) and the
hub runs **its own network**, the image is **fully self-contained** — in the
common case there is **nothing to inject**. An *optional* file on the boot
partition covers the few deviations (Wi-Fi uplink, custom AP name, hostname).

End-user flow:

1. Insert the SD card, plug the Pi into **ethernet + power**.
2. *(optional)* drop an `evohub.conf` on the boot partition for any overrides.
3. Power on — the hub comes up on its own Wi-Fi + the dashboards.

A Claude Code skill can additionally drive the flashing and verify the result,
but the image works on its own.

### Non-goals (this iteration)

- Multi-hub fleet orchestration / central management.
- The experimental **MinIO** and **Prefect** stacks (not shipped).
- Auto-migrating the existing live hub at the lab (handled separately).

## 1. Where we are today (grounded reality)

The current README flow needs a monitor at first boot, manual `apt`/Docker
install, an external USB HDD, and Portainer copy-paste. Useful prior art exists
but is **abandoned WIP** — mine it for the *steps*, don't adopt the tooling:

| Prior art | Branch | Salvage value | State |
|---|---|---|---|
| Ansible roles | `refactor-playbooks-into-roles` | the exact install steps (apt deps, Docker, GitHub key, clone, Portainer) | abandoned, ~2 yrs old, never merged; `build_evohub_images` broken |
| USB mount + `docker compose up` | `14-use-ansible-…` | USB auto-mount logic; already off Portainer-paste | abandoned WIP |
| Docker log rotation | `claude/keen-maxwell` (Mar 2026) | `daemon.json` (50 MB ×3) | **bake in** |

**Ansible is not used anywhere on `main`** and the live hub was set up by hand —
so we treat Ansible as a reference, not a foundation, and build with plain shell.

### Reality gaps to fix along the way

- **Stale external-HD assumption**: the log-rotation incident (15 GB of logs
  filled a 29 GB SD card and broke Grafana) shows data lives on the SD card, not
  the `~/data` external disk the README assumes.
- **Four network numbers** drift across the repos (`10.66.4.x`, `192.168.31.x`,
  `192.168.1.x`, `172.16.0.x`) — collapse to one model (below).
- **Hub-internal services point at the hub's own external IP** (`.env`
  `DB_HOST`/`MQTT_HOST = 10.66.4.7`) — a portability bug; must use compose
  service names.
- **mosquitto volume triple-mount bug** (one named volume at config/data/log);
  **Python 3.11 base vs `>=3.12` deps**; **AP is documented but never deployed**
  (the hub is currently a Wi-Fi *client* of a separate router).

> Note: committed service passwords are **intentionally kept** — they are
> non-sensitive public defaults by the project's own call. The `.env` change
> below is about *correctness/portability* (don't route to yourself via an
> external IP), not secrecy.

## 2. Target architecture (end state)

A **one-box appliance**:

- Pi runs **backend** (Postgres, Mosquitto, Grafana) + **apps** (listener, UI)
  via one `docker compose` stack under a **systemd** unit (`restart: always`).
  **No Portainer.**
- **Hub is its own Wi-Fi AP** (`hostapd` + `dnsmasq` on onboard `wlan0`) for the
  reactor network, with an **ethernet uplink** for internet/lab access. Reactors
  join the hub's AP; the dongle/Wi-Fi-uplink variant is in §7 / D2.
- **Container images pulled from GHCR** (arm64), not built on the Pi.
- **Baked public defaults** for all service config.

```
   lab ethernet  (user finds the hub's IP here, as today — it's DHCP)
        │
   ┌────┴─────┐   wlan0 = AP "evo-net"  ──┬── Pico reactor   → mqtt 192.168.4.1
   │  EvoHub  │   (hostapd + dnsmasq,     ├── Pico reactor
   │   (Pi)   │    gateway 192.168.4.1)   └── (laptop, if it joins the AP)
   └──────────┘
   docker compose: postgres · mosquitto · grafana · listener · ui
```

### IP model (the single source of truth)

| Who talks | To what address |
|---|---|
| Hub's own containers (listener/UI → Postgres/Mosquitto) | **compose service names** (`postgres`, `mosquitto`) — never an IP |
| Reactors → broker | the **fixed AP gateway** `192.168.4.1` (hub is the DHCP server, so this never changes) |
| Human → Grafana/UI | the hub's **IP on whatever network they're on** — user-determined (DHCP on the lab side, exactly like today). No mDNS. |

After this, no hardcoded IP survives in the runtime; the only IP constant is the
reactors' `mqtt_host = 192.168.4.1`.

## 3. Image model: baked image + optional override

**Layer A — the golden image** (identical for every lab, self-contained):

- Raspberry Pi OS Lite **arm64**, headless, **SSH pre-enabled** (baked public key;
  private key stays on the operator's laptop).
- Docker + compose plugin; `daemon.json` **log rotation** pre-installed.
- The merged `docker-compose.yml` + configs with **baked public defaults**;
  container images **pre-pulled** from GHCR (works offline on first boot).
- `hostapd`/`dnsmasq` configured for the **default AP** (SSID `evo-net`, gateway
  `192.168.4.1`); NAT to `eth0`.
- A **systemd unit** that runs `docker compose up -d` on boot.

**Layer B — optional override** (only if you deviate from defaults):

- An optional **`evohub.conf`** on the FAT **boot partition** (editable on any OS,
  no network). A first-boot oneshot reads it **only if present** to set:
  Wi-Fi uplink creds, a custom AP SSID/passphrase (for multi-hub), or a hostname.
- If absent → the image runs on pure defaults. No required injection step.

This replaces v1's mandatory "credential injection layer": the image is complete
on its own, and the override file is a thin escape hatch.

## 4. Configuration (baked defaults)

All baked into the image; all non-sensitive public defaults by design:

| Item | Baked default | Overridable via `evohub.conf`? |
|---|---|---|
| Postgres db/user/pass | `postgres` / `postgres` / `postgres` | no (not needed) |
| Grafana admin | `admin` / `veryhungryphage` | no |
| MQTT service user/pass | `service_account` / `service_pass` | no |
| Hub-internal DB/MQTT host | service names `postgres` / `mosquitto` | no |
| AP SSID / passphrase | `evo-net` / `hungryphage` (matches the reactor default) | yes (multi-hub) |
| AP gateway IP | `192.168.4.1/24` | no |
| Uplink | ethernet (DHCP) | **yes — Wi-Fi creds** (the one genuine per-site secret) |
| Hostname | `evohub` | yes |

The only injection that ever carries a real secret is the **Wi-Fi-uplink
variant** (a lab Wi-Fi password) — and only if you don't use ethernet.

## 5. Build the image (shell, no Ansible)

- **Primary: `pi-gen`** (the official Raspberry Pi OS builder) with a custom
  **shell stage** that performs the install recipe. Runs in CI/Docker, outputs
  `evohub-vX.Y.img.xz`.
- **Pragmatic fallback:** provision one **reference Pi** with the recipe by hand,
  then capture it with `pishrink`/`dd`. Crude but fast for the first cut.
- **Mine the abandoned Ansible roles** for the recipe contents — they already
  worked out: apt deps (`docker.io`, `hostapd`, `dnsmasq`, `dhcpcd`, …), Docker
  install + group + socket perms, data-dir layout, USB auto-mount.

Recipe (shell): base image → apt deps + Docker → `daemon.json` log rotation →
copy compose + configs + AP config → `docker compose pull` (pre-pull GHCR
images) → install systemd unit + optional first-boot hook → enable SSH key.

## 6. Container images → GHCR

- CI builds **arm64** `idec_base` / `evoflow_listener` / `evoflow_ui` via `buildx`,
  pushes to `ghcr.io/schwank-lab/*`.
- **Removes the SSH-key-in-image hack**: `evoflow_db`/`evoflow_utils` are
  subdirectories of this same repo, so CI installs them as **local path deps**
  instead of `git@github` deps — no deploy key on the Pi.
- Compose pins GHCR tags; image pre-pulls them. Updates = `docker compose pull && up -d`.

## 7. Networking: hub-as-AP

Productionize the README's never-deployed `hostapd`/`dnsmasq` recipe:

- `wlan0` static **`192.168.4.1/24`**; `dnsmasq` DHCP range on that subnet;
  `hostapd` SSID **`evo-net`** / passphrase `hungryphage` (the existing reactor
  defaults, so reactors associate unchanged); **NAT** `wlan0 → eth0`.
- **Reactor change (one line):** `evoflow-reactor/pico/configs/default-network_config.json`
  `mqtt_host` `192.168.31.10` → **`192.168.4.1`**.
- **Dongle only for the Wi-Fi-uplink variant** (D2): onboard radio can't be AP +
  Wi-Fi-client at once, so a USB Wi-Fi dongle gives the second radio. With
  ethernet uplink, no dongle.

## 8. Claude Code provisioning skill (optional UX layer)

The image works without it, but the skill makes it turnkey:

1. Prompts for any overrides (else pure defaults); generates none (defaults are baked).
2. Drives **`rpi-imager --cli <img> /dev/diskN`** to flash, with a **hard confirm
   on the destructive write**.
3. *(optional)* writes `evohub.conf` to the boot partition.
4. After boot, connects to the hub **over the AP** (`192.168.4.1`, known —
   no discovery needed) or a user-provided IP, runs **health checks**, and
   **prints the live URLs + the global IP it observes** (so the user has the
   actual dashboard address without mDNS).

Biologist's steps: insert card, plug in ethernet+power, run Claude, confirm the flash.

## 9. Repo changes (concrete worklist)

- **Compose**: merge `backend_stack` + `monitor_stack` into one `docker-compose.yml`;
  fix `.env` `DB_HOST`/`MQTT_HOST` → service names; fix mosquitto triple-mount;
  pin GHCR tags; align Python to 3.12.
- **Networking**: `hostapd`/`dnsmasq`/`dhcpcd` config + NAT + systemd enablement.
- **Image build**: `pi-gen` config (or reference-Pi capture) + CI workflow →
  `evohub-vX.Y.img.xz`.
- **CI**: GHCR arm64 `buildx` build/push for the three images.
- **First-boot (optional)**: oneshot that reads `evohub.conf` overrides + an
  `evohub.conf.example`.
- **Skill**: `.claude/skills/provision-evohub`.
- **Docs**: rewrite README to the image flow; "open Grafana at `http://<hub-ip>:3000`"
  (user supplies the IP); keep a manual/advanced appendix.
- **Reactor repo**: `mqtt_host` default → `192.168.4.1`; update the `mqtt-cli/*`
  and `pico-bridge/config.py` debug hosts.
- **Dropped from v1**: secret purge/rotation (keep public defaults); Avahi/mDNS.

## 10. Milestones (working end-to-end early)

| # | Milestone | Proves |
|---|---|---|
| **M1** | Consolidate runtime: one `docker-compose.yml` with baked defaults; `.env` → service names; `docker compose up -d` brings the full hub up on any Docker host | the stack runs self-contained |
| **M2** | Boot autostart: systemd unit runs compose on boot; optional `evohub.conf` hook; tested on a stock-flashed Pi | boot-to-running |
| **M3** | GHCR images: CI builds/pushes arm64; Pi **pulls** instead of builds | no on-Pi build, no SSH-key hack |
| **M4** | Networking: hub-as-AP; reactors associate at `192.168.4.1`; end-to-end with a real/fake reactor | the appliance topology |
| **M5** | Golden image: shell/`pi-gen` build with images pre-pulled; flash → boot → running appliance | the shippable artifact |
| **M6** | Claude skill: flash + (optional config) + health-check + print URLs/IP | the biologist UX |

## 11. Risks & mitigations

- **Destructive flash** (`rpi-imager` raw write) → explicit device confirmation;
  never auto-select a disk.
- **Image distribution** (>2 GB GitHub asset limit) → `xz`-compress; GitHub Release.
- **Offline time drift** — schema is timestamp-keyed, an isolated AP island has no
  NTP → keep the ethernet uplink, or add an RTC; document.
- **Onboard-radio AP limits** (client count/range) → dongle + external antenna
  option per site (D2).
- **SD-card fill/wear** (already bit them) → log rotation baked in; consider
  Postgres data on the external disk / a quality SD; monitor free space.
- **arm64-only** → `buildx` in CI; test on real Pi 4/5.

*(Secret-leakage risk dropped: no secrets — public defaults by design.)*

## 12. Open decisions

- **D2 — Uplink**: ethernet (**baseline** — no creds, no dongle) vs Wi-Fi (needs
  a USB dongle so the radio can be AP + client, **and** the one piece of
  credential injection).
- **D3 — Image tool**: `pi-gen` shell stage (**recommended**) vs reference-Pi +
  `pishrink`/`dd` (faster first cut).
- **D5 — Hardware baseline**: Pi 4 vs Pi 5; SD vs SSD; external data disk yes/no.

*Decided:* hub-as-AP (D1); drop Portainer for compose+systemd (D4); no Ansible;
no mDNS; bake public defaults.

---

## Changelog v1 → v2

- **Ansible dropped.** It was never adopted (abandoned 2024 WIP, not on `main`).
  Image is built with plain shell (`pi-gen`); the old roles are mined for steps only.
- **Public defaults, injection optional.** No sensitive data, so service configs
  are baked from the existing defaults; the mandatory "credential injection layer"
  becomes an *optional* `evohub.conf` override for Wi-Fi uplink / AP name / hostname.
- **IP model fixed.** Hub-internal → compose service names; reactors → fixed AP
  gateway `192.168.4.1`; humans → user-determined IP.
- **mDNS removed.** No `evohub.local`/Avahi; the setup *prints* the live IP instead.
- **hub-as-AP is the baseline** (was an open decision).
- **Milestones reordered** around the simpler, mostly-baked design.
