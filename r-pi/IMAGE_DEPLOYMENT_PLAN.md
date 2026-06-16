# EvoHub Image-Based Deployment — Plan

Status: **draft / proposal** · Branch: `image-based-deployment`

## 0. Goal

A non-technical user (a biologist) can bring up a complete, working EvoHub with
**no monitor, no keyboard, no copy-paste, and no shell commands they have to
understand** — ideally driven end-to-end by Claude Code on their laptop. The
mechanism is a **pre-baked SD-card image** (identical for every lab) plus
**injection of credentials / site config at first boot** (the only per-lab part).

Target end-user flow:

1. Insert the SD card, plug the Pi into **ethernet + power**.
2. Run Claude Code, say "set up my EvoHub".
3. Answer ~2 prompts (Wi-Fi name/password for the reactor network).

Everything else — flashing, config injection, service bring-up, health checks —
is automated.

### Non-goals (for this iteration)

- Multi-hub fleet orchestration / central management.
- The experimental **MinIO** and **Prefect** stacks (out of scope; not shipped).
- Auto-migrating the existing live hub at `10.66.4.7` (handled separately).

## 1. Where we are today (grounded reality)

The current README flow needs a monitor at first boot, manual `apt`/Docker
install, an external USB HDD, and Portainer copy-paste. But a lot of automation
already exists in branches and should be **reused, not rebuilt**:

| Prior art | Branch | What it gives us | State |
|---|---|---|---|
| Ansible roles | `refactor-playbooks-into-roles` | `apt`, `docker`, `github`, `clone`, `build_evohub_images`, `portainer`, `install_lab` | WIP; `build_evohub_images` broken (empty `ssh_private_key`, var-name mismatch) |
| USB mount + `docker compose up` | `14-use-ansible-to-deploy-evohub-monitor-stack` | `install_docker_stack.yml`: auto-mounts USB, creates data dirs, `docker compose up -d` | works; already off Portainer-paste |
| Portainer-API deploy + `.secrets` | `14-…` | `deploy_{backend,monitor}_stack.sh` source creds from a `.secrets` file | precursor to cred injection |
| Docker log rotation | `claude/keen-maxwell` (Mar 2026) | `daemon.json` (50 MB ×3) in `installme.sh` | **must bake in** |

### Reality gaps to fix along the way

- **Secrets committed in cleartext**: `evoflow_utils/.env` (`DB_PASS=postgres`,
  `MQTT_PASS=service_pass`), `backend_stack.yml` (`POSTGRES_PASSWORD=postgres`,
  `GF_SECURITY_ADMIN_PASSWORD=veryhungryphage`), `minio_stack.yml`
  (`hungryphage`), `prefect_stack.yml` (AWS-style keys), README AP passphrase
  `cicciociccio`, reactor `evo-net`/`hungryphage`. All must move to first-boot
  generation; the live ones must be rotated.
- **Four different network numbers** drift across the repo (`10.66.4.x`,
  `192.168.31.x`, `192.168.1.x`, `172.16.0.x`) — collapse to one source of truth
  (`evohub.local` + injected config).
- **External-HD assumption is stale**: the log-rotation incident shows data
  lives on a 29 GB SD card, not the `~/data` external disk the README assumes.
- **Python 3.11 base vs `>=3.12` deps**; **mosquitto volume triple-mount bug**
  (one named volume mounted at config/data/log); **AP is documented but never
  deployed** (the hub is currently a Wi-Fi client of a separate router).

## 2. Target architecture (end state)

A **one-box appliance**:

- Pi runs **backend** (Postgres, Mosquitto, Grafana) + **apps** (listener, UI)
  via a single `docker compose` stack under a **systemd** unit (`restart: always`,
  survives reboot). No Portainer required.
- **Networking (recommended): hub is its own Wi-Fi AP** (`hostapd` + `dnsmasq`
  on onboard `wlan0`) for the reactor "local" network, with **ethernet uplink**
  for internet/"global". The reactors join the hub's AP; the laptop reaches the
  hub at `evohub.local`. A USB Wi-Fi dongle is only needed if a given site has
  **no ethernet** and both sides must be wireless. *(See Decision D1.)*
- **Container images pulled from GHCR** (arm64), not built on the Pi.
- **No secret in the image or the repo** — all generated or injected at first boot.

```
   lab ethernet (no credentials — just plug in)
        │
   ┌────┴─────┐   wlan0 = AP "evo-net"  ──┬── Pico reactor
   │  EvoHub  │   (hostapd + dnsmasq)     ├── Pico reactor
   │   (Pi)   │                           └── biologist laptop → Claude / Grafana
   └──────────┘
   docker compose: postgres · mosquitto · grafana · listener · ui
```

## 3. The two-layer model: generic image + injected config

This is the heart of the design. Keep the image **generic and shareable**; push
everything secret or site-specific into a tiny first-boot config.

**Layer A — the golden image** (identical for every lab, contains no secrets):

- Raspberry Pi OS Lite **arm64**, headless.
- **SSH pre-enabled** with a baked provisioning **public** key (private key lives
  only on the operator's laptop / in the Claude skill).
- Docker + compose plugin; `daemon.json` log rotation pre-installed.
- The repo's compose + config **templates**; container images **pre-pulled** from
  GHCR so the hub works even before it has internet.
- `hostapd`/`dnsmasq` installed but **inert** until first-boot config enables them.
- Data dirs + fstab prepared; a **first-boot systemd oneshot** installed.

**Layer B — first-boot injection** (per-lab, secret, written by the operator):

- A single human-editable file, **`evohub.conf`**, dropped on the **boot
  partition** (FAT — mountable on macOS/Windows/Linux with no tools, no network).
- Holds: hostname, **AP SSID + passphrase**, optional uplink Wi-Fi creds, and
  either explicit service passwords or a `generate=true` flag.
- The first-boot oneshot reads it, **generates any missing secrets**, templates
  every config, brings the stack up, creates DB tables, health-checks, then
  **disables itself**.

Why this split: a baked-in image can't know a lab's Wi-Fi or carry per-lab
secrets safely; Ansible-vault alone assumes the biologist runs Ansible. A
boot-partition file is the one channel that is headless, offline, cross-OS, and
writable by the Claude skill.

## 4. Credential / config injection — the core deliverable

Inventory of what must be injected or generated (grounded in the secret sweep):

| Item | Today (committed) | New source at first boot |
|---|---|---|
| Postgres password | `postgres` | **generated** |
| Grafana admin password | `veryhungryphage` | generated (or injected) |
| MQTT service user/pass | `service_account` / `service_pass` | generated → mosquitto `pwfile` |
| Reactor-network AP SSID + passphrase | `evo-net` / `hungryphage`, README `cicciociccio` | **injected** (operator-chosen, per lab) |
| Reactor Wi-Fi creds | committed in reactor repo | **= the AP creds**, shared via `evotool init` |
| Hostname / host IPs | `10.66.4.7` etc. hardcoded | `evohub.local` (mDNS) + injected |
| MinIO / Prefect AWS keys | committed | **removed** from shipped stacks |

Flow: `evohub.conf` → first-boot oneshot → renders `.env` (consumed by compose &
the Python `Config`), `mosquitto` `pwfile`, Grafana admin env, and `hostapd.conf`.
Generated secrets are persisted to the data volume **and surfaced back to the
operator** (printed by the Claude skill / written to a file it reads after SSH).

## 5. Reuse & complete the Ansible roles

The existing roles become the **single source of provisioning logic**, runnable in
two modes:

- **Build-time** (CI, against the mounted image / chroot) → bakes the golden image.
- **Run-time** (optional, over SSH against a live Pi) → for iterating on the
  playbooks and for updating an already-deployed hub.

Work needed:

- **Port** the roles forward onto current `main` (they predate recent app work).
- **Fix/replace `build_evohub_images`**: drop the broken local Docker build with
  the empty SSH key; instead **pull images from GHCR** (see §6). Keep a build
  path only for CI.
- **Parameterize** `ansible_user`, repo, and all networking vars.
- **New roles**:
  - `network_ap` — `hostapd` + `dnsmasq` + `dhcpcd` static IP + NAT to `eth0`
    (productionize the README's hostapd recipe, currently undeployed).
  - `compose_stack` — replace the Portainer-API scripts with one
    `docker compose` stack + a systemd unit.
  - `log_rotation` — `daemon.json` (fold in `claude/keen-maxwell`).
  - `first_boot` — install the oneshot + config templates + `evohub.conf.example`.
- One top-level playbook `install_appliance.yml` composing the above.

## 6. Container images → GHCR

- CI builds **arm64** `idec_base` / `evoflow_listener` / `evoflow_ui` via `buildx`
  and pushes to `ghcr.io/schwank-lab/*`.
- **Removes the SSH-key-in-image hack**: `evoflow_db` / `evoflow_utils` are
  *subdirectories of this same repo*, so the CI build installs them as **local
  path deps** instead of `git@github` deps — no deploy key on the Pi at all.
- Compose pins GHCR tags; the image build **pre-pulls** them so first boot is
  offline-capable. Updates become `docker compose pull && up -d`.

## 7. Claude Code provisioning skill (the biologist UX)

A repo skill `provision-evohub` that:

1. Prompts for **AP SSID + passphrase** and optional uplink Wi-Fi / hostname;
   **generates** all service passwords.
2. Downloads the released image and drives **`rpi-imager --cli <img> /dev/diskN`**
   to flash the chosen SD device — with a **hard confirm on the destructive
   write** (the one genuinely dangerous step).
3. Writes **`evohub.conf`** (and re-asserts the SSH key) onto the boot partition
   (`/Volumes/bootfs` on macOS).
4. Waits for boot, discovers **`evohub.local`** via mDNS, SSHes in with the baked
   key, watches the first-boot oneshot, and runs **health checks** on every service.
5. Prints the **generated passwords + URLs** (Grafana `http://evohub.local:3000`,
   the UI, the DB) and optionally exercises the data path with `fake_reactor`.

Biologist's literal steps remain: insert card, plug in ethernet+power, run Claude,
answer 2 prompts.

## 8. Repo changes (concrete worklist)

- **Security**: purge committed secrets; rotate the live ones; `.gitignore` the
  stray in-repo `.venv/` dirs; delete MinIO/Prefect AWS keys from shipped stacks.
- **Compose**: merge `backend_stack` + `monitor_stack` into one env-driven
  `docker-compose.yml`; fix the mosquitto triple-mount; pin GHCR tags;
  align Python to 3.12 across base + packages.
- **Ansible**: bring roles to `main`; complete/replace `build_evohub_images`;
  add `network_ap`, `compose_stack`, `log_rotation`, `first_boot`; add
  `install_appliance.yml`.
- **Image**: add the image-build config + CI workflow producing
  `evohub-vX.Y.img.xz`.
- **CI**: add GHCR arm64 build/push for the three images.
- **First-boot**: oneshot script + config templates + `evohub.conf.example`.
- **Skill**: `.claude/skills/provision-evohub`.
- **Docs**: replace the manual README with the image flow; keep a manual/advanced
  appendix.

## 9. Milestones (ordered so there is a working end-to-end early)

| # | Milestone | Proves |
|---|---|---|
| **M1** | Consolidate & de-secret: merged env-driven compose; `docker compose up` brings the hub up from an injected `.env` on a manually-booted Pi | the runtime works without Portainer or committed secrets |
| **M2** | First-boot injection: oneshot reads `evohub.conf` → templates → `compose up`, on a **stock**-flashed Pi (Imager headless) | injection works before any custom image exists |
| **M3** | GHCR images: CI builds/pushes arm64; Pi **pulls** instead of builds | no on-Pi build, no SSH-key hack |
| **M4** | Golden image: CI bakes the image (Ansible-in-build) with images pre-pulled; flash → boot → running | the shippable artifact |
| **M5** | Networking: `network_ap` role; reactors associate to the hub AP; end-to-end with a real/fake reactor | the appliance topology |
| **M6** | Claude skill: flash + inject + verify; full biologist run-through | the end-user experience |

Each milestone is independently useful and testable; M1–M2 give a working
injected deployment long before the image pipeline exists.

## 10. Risks & mitigations

- **Destructive flash** (`rpi-imager` raw write) → explicit device confirmation in
  the skill; never auto-select a disk.
- **Image distribution** (>2 GB GitHub asset limit) → `xz`-compress; host as a
  GitHub Release / Imager image-list URL.
- **Offline time drift** — the schema is timestamp-keyed, an isolated AP island
  has no NTP → keep the ethernet uplink, or add an RTC module; document.
- **Onboard-radio AP limits** (client count / range) → USB dongle + external
  antenna option per site (Decision D1).
- **SD-card fill / wear** (already bit them: 15 GB of logs) → log rotation baked
  in; consider moving Postgres data to the external disk or a quality SD; monitor
  free space.
- **arm64-only** image/containers → `buildx` in CI; test on real Pi 4/5.
- **Secret leakage** → never in image/repo; generate at first boot; print once.

## 11. Open decisions (need a call before building)

- **D1 — Networking**: hub-as-AP (**recommended**, one box) vs keep a separate
  router. Drives whether the image ships `hostapd`/`dnsmasq` active and whether a
  dongle is in the kit.
- **D2 — Uplink**: ethernet (**recommended**, no creds, reliable mDNS) vs Wi-Fi
  (needs a dongle so the radio can be AP + client).
- **D3 — Image tool**: `packer-builder-arm` + Ansible provisioner (**recommended**
  — natively reuses the existing roles) vs `pi-gen` (official) vs provision-a-
  reference-Pi-then-`pishrink`/`dd` (pragmatic fallback).
- **D4 — Portainer**: drop in favor of compose + systemd (**recommended**) vs keep
  as an optional GUI.
- **D5 — Hardware baseline**: Pi 4 vs Pi 5; SD vs SSD; external data disk yes/no.
