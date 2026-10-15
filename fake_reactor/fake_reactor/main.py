"""Simulate one EvoFlow reactor, to test an EvoHub without hardware.

Does what Evotool and a running reactor do together: registers a reactor and a
started experiment in the hub's database, then publishes the reactor's state to
the hub's MQTT broker every few seconds, in the format an EvoBridge forwards.
The experiment then appears in the EvoMonitor dashboard like a real one.
"""

import argparse
import itertools
import json
import random
import time

import paho.mqtt.client as mqtt
import psycopg2

# The EvoHub's public defaults (r-pi/docker/evohub.env).
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASS = "postgres"

STATE_TOPIC = "status/experiment"

# A turbidostat on the right incubator: the culture grows until it reaches the
# target optical density, then fresh medium dilutes it back down.
TARGET_OD = 0.7
GROWTH_PER_STEP = 1.05
DILUTION_ML = 2.0
LAGOON_FLOW_RATE = 0.5


def register(conn, reactor_name: str, experiment_name: str) -> int:
    """Create the reactor (unless it exists) and a started experiment.

    Returns the new experiment's id, which every published state carries.
    """
    with conn, conn.cursor() as cur:
        cur.execute("SELECT reactor_id FROM reactor WHERE name = %s", (reactor_name,))
        row = cur.fetchone()
        if row is None:
            cur.execute(
                "INSERT INTO reactor (name, network_id) VALUES (%s, %s) RETURNING reactor_id",
                (reactor_name, "0.0.0.0"),
            )
            row = cur.fetchone()
        cur.execute(
            "INSERT INTO experiment (reactor_id, name, status, timestamp) "
            "VALUES (%s, %s, 'start', %s) RETURNING experiment_id",
            (row[0], experiment_name, int(time.time())),
        )
        return cur.fetchone()[0]


def grow(od: float) -> tuple[float, float]:
    """One step of turbidostat growth. Returns the new OD and the volume diluted."""
    od *= GROWTH_PER_STEP
    if od < TARGET_OD:
        return od, 0.0
    return TARGET_OD * 0.9, DILUTION_ML


def state(experiment_id: int, od: float, total_dilution: float) -> dict:
    """A reactor state message, with the keys the EvoHub listener stores.

    The left incubator is unused, which the reactor reports as -1.
    """
    return {
        "experiment_id": experiment_id,
        "timestamp": time.time(),
        "lagoon_temp": round(random.gauss(37.0, 0.1), 2),
        "lagoon_flow_rate": LAGOON_FLOW_RATE,
        "inc_left_temp": -1,
        "inc_left_od": -1,
        "inc_left_dilution": -1,
        "inc_right_temp": round(random.gauss(37.0, 0.1), 2),
        "inc_right_od": round(od, 4),
        "inc_right_dilution": total_dilution,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--hub", default="evohub.local", help="EvoHub address (default: evohub.local)")
    parser.add_argument("--reactor", default="FakeReactor", help="reactor name (default: FakeReactor)")
    parser.add_argument("--experiment", default=f"fake-{time.strftime('%Y%m%d-%H%M%S')}", help="experiment name")
    parser.add_argument("--interval", type=float, default=5.0, help="seconds between states (default: 5)")
    parser.add_argument("--count", type=int, help="stop after this many states (default: run until Ctrl+C)")
    args = parser.parse_args()
    assert args.interval > 0, "--interval must be positive"

    conn = psycopg2.connect(host=args.hub, port=5432, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    experiment_id = register(conn, args.reactor, args.experiment)
    conn.close()
    print(f"Registered experiment '{args.experiment}' (id {experiment_id}) on reactor '{args.reactor}'.")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"fake-reactor-{args.reactor}")
    client.connect(args.hub, 1883)
    client.loop_start()

    od, total_dilution = 0.3, 0.0
    steps = itertools.count() if args.count is None else range(args.count)
    for _ in steps:
        od, diluted = grow(od)
        total_dilution += diluted
        message = state(experiment_id, od, total_dilution)
        client.publish(STATE_TOPIC, json.dumps(message)).wait_for_publish()
        print(f"published OD {message['inc_right_od']:.3f}, dilution {total_dilution:.1f} ml")
        time.sleep(args.interval)

    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":
    main()
