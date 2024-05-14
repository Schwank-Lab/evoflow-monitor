import pytest
from unittest.mock import mock_open, patch
from fake_reactor.csv_reader import (
    CSVReader,
)
import json


@pytest.fixture
def mock_csv_file():
    csv_content = (
        "timestamp,inc_od,inc_temp,lagoon_temp,lagoon_flow_rate\n"
        "0,None,37.0,34.875,1\n"
        "3,0.4754047,37.0,34.9375,1"
    )

    with patch("builtins.open", mock_open(read_data=csv_content)) as mock_file:
        yield mock_file


def test_read_lines(mock_csv_file):
    reader = CSVReader("dummy_path.csv")
    result = list(reader.read_lines())

    assert len(result) == 2, "Expected two dictionaries but got a different number"

    assert isinstance(result[0], dict), "Expected dictionary but got another type"
    assert isinstance(result[1], dict), "Expected dictionary but got another type"

    expected_keys = {
        "timestamp",
        "inc_od",
        "inc_temp",
        "lagoon_temp",
        "lagoon_flow_rate",
    }
    assert (
        set(result[0].keys()) == expected_keys
    ), "Dictionary keys for the first line do not match expected keys"
    assert (
        set(result[1].keys()) == expected_keys
    ), "Dictionary keys for the second line do not match expected keys"

    assert result[0] == {
        "timestamp": "0",
        "inc_od": "None",
        "inc_temp": "37.0",
        "lagoon_temp": "34.875",
        "lagoon_flow_rate": "1",
    }, "Dictionary contents for the first line do not match expected contents"

    assert result[1] == {
        "timestamp": "3",
        "inc_od": "0.4754047",
        "inc_temp": "37.0",
        "lagoon_temp": "34.9375",
        "lagoon_flow_rate": "1",
    }, "Dictionary contents for the second line do not match expected contents"


def test_to_json_and_back(mock_csv_file):
    reader = CSVReader("dummy_path.csv")
    lines = reader.read_lines()
    # Iterate over each row from the CSV, converted to JSON
    for json_str in reader.to_json():
        deserialized_dict = json.loads(json_str)

        original_dict = next(lines)

        assert isinstance(
            deserialized_dict, dict
        ), "Expected dictionary but got another type"

        # Assert that the deserialized dictionary matches the original dictionary
        assert (
            deserialized_dict == original_dict
        ), "The deserialized dictionary does not match the original"

        for key in original_dict:
            assert (
                deserialized_dict[key] == original_dict[key]
            ), f"Mismatch in {key} field"
