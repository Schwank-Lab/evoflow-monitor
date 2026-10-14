# fake_reactor

Simulates one EvoFlow reactor, to test an EvoHub before any reactor is connected.

It does what Evotool and a running reactor do together: registers a reactor and
a started experiment in the hub's database, then publishes the reactor's state
to the hub's MQTT broker every few seconds, in the format an EvoBridge forwards.
The right incubator runs as a turbidostat (OD grows to 0.7, then is diluted), so
every EvoMonitor panel shows a live trace.

```bash
poetry install
poetry run fake-reactor                       # hub at 192.168.4.1 (from evo-net), until Ctrl+C
poetry run fake-reactor --hub evohub.local --count 20 --interval 2
poetry run fake-reactor --help
```

Each run creates a new experiment, the newest one, which EvoMonitor opens on; reactor `FakeReactor` is created once and reused.
