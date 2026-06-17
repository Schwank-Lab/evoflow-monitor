# EvoFlow Monitor — EvoHub

**EvoHub** is the central hub for the EvoFlow PACE bioreactor fleet. It collects
telemetry from every reactor, stores it, shows it on dashboards, and sends
control commands back to the reactors.

## What it does

- **Collect** experiment data the reactors publish over MQTT.
- **Store** it in PostgreSQL (reactors, experiments, configs, time-series state).
- **Visualise** it in Grafana dashboards.
- **Control** experiments from a web UI (start / stop / pause, create experiments,
  change flow rate) — pushed back to the reactors over MQTT.

## Architecture

```
                Reactors  (Raspberry Pi Pico W)
                    │                ▲
       status/experiment        commands
       status/reactor               │
                    ▼                │
   ┌──────────────────── EvoHub ─────┴───────────────┐
   │                                                  │
   │     Mosquitto  (MQTT broker, the message bus)    │
   │        │                         ▲               │
   │        ▼                         │               │
   │   listener ───► PostgreSQL ◄──── UI (Dash web)   │
   │                    │                             │
   │                 Grafana (dashboards)             │
   │                                                  │
   └──────────────────────────────────────────────────┘
            all services run as Docker containers
```

### Components

| Component | Role |
|---|---|
| **Mosquitto** | MQTT broker — the message bus between reactors and the hub |
| **PostgreSQL** | stores reactors, experiments, configs, and time-series state |
| **Grafana** | dashboards over the database |
| **evoflow_listener** | subscribes to reactor telemetry and writes it to the DB |
| **evoflow_ui** | Dash web app — shows live state and sends control commands |
| **evoflow_db** | shared SQLAlchemy models + DB engine (used by listener & UI) |
| **evoflow_utils** | shared config (`.env`) + MQTT client wrapper |

### How messages flow

Everything is MQTT publish/subscribe through Mosquitto:

| Topic | Direction | Payload | Consumer |
|---|---|---|---|
| `status/experiment` | reactor → hub | OD / temp / dilution / flow-rate, + `experiment_id`, timestamp | **listener** → persisted to `experiment_state` |
| `status/reactor` | reactor → hub | live reactor state, keyed by `reactor_id` | **UI** (kept in memory, ~10 s) |
| `commands` | hub → reactor | `{reactor_id, command, …}` (start/stop/pause, new/update experiment) | reactors |

So telemetry flows **reactor → `status/experiment` → listener → DB → Grafana**,
and control flows the other way: **UI → `commands` → reactor**.

### Data model

`reactor` ─< `experiment` ─< (`experiment_state` time-series, `experiment_config`),
and `reactor` ─< `reactor_config`. SQLAlchemy models live in `evohub/evoflow_db`.

## Deploying

The hub is just a set of Docker services, so it can run on any always-on Linux
box. The **supported deployment is a self-contained Raspberry Pi appliance**: a
pre-built SD image that boots straight into the whole stack and also acts as the
reactor fleet's Wi-Fi access point.

➡️ **See [`r-pi/`](./r-pi)** for the appliance — download, flash, boot.

The earlier from-scratch manual process is preserved in
[`r-pi/legacy-manual-setup.md`](./r-pi/legacy-manual-setup.md) (superseded).

## Repository layout

| Path | What |
|---|---|
| `evohub/` | the hub services + shared packages (`evoflow_listener`, `evoflow_ui`, `evoflow_db`, `evoflow_utils`) |
| `r-pi/` | the Raspberry Pi appliance deployment (image build + docs) |
| `fake_reactor/` | replays recorded data onto MQTT to exercise the pipeline without hardware |
