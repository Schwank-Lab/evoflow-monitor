from fake_reactor.main import TARGET_OD, grow, state

# The keys the EvoHub listener reads from every state message
# (evohub/evoflow_listener/evoflow_listener/mqtt_listener.py).
LISTENER_KEYS = {
    "experiment_id", "timestamp", "lagoon_temp", "lagoon_flow_rate",
    "inc_left_temp", "inc_left_od", "inc_left_dilution",
    "inc_right_temp", "inc_right_od", "inc_right_dilution",
}


def test_state_has_exactly_the_listener_keys():
    assert set(state(1, 0.5, 0.0)) == LISTENER_KEYS


def test_grow_dilutes_at_the_target_od():
    od, diluted = grow(TARGET_OD)
    assert od < TARGET_OD
    assert diluted > 0


def test_grow_does_not_dilute_below_the_target_od():
    od, diluted = grow(0.3)
    assert 0.3 < od < TARGET_OD
    assert diluted == 0
