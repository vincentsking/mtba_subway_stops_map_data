
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app, make_a_request
import time
import json
from deepdiff import DeepDiff

client = TestClient(app)

# -------------------------------
# Unit Test: make_a_request
# -------------------------------
@patch("main.requests.get")
def test_make_a_request_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "ok"}
    mock_get.return_value = mock_response

    result = make_a_request("https://example.com")
    assert result.status_code == 200
    assert result.json() == {"data": "ok"}


@patch("main.requests.get")
def test_make_a_request_429_retry(mock_get):
    # First call returns 429, second returns 200
    mock_429 = MagicMock()
    mock_429.status_code = 429
    mock_429.headers = {"x-ratelimit-reset": str(int(time.time()) + 1)}

    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.json.return_value = {"data": "ok"}

    mock_get.side_effect = [mock_429, mock_200]

    result = make_a_request("https://example.com")
    assert result.status_code == 200


# -------------------------------
# Integration Test: /stops endpoint
# -------------------------------
@patch("main.get_subway_lines")
@patch("main.get_subway_line_stops")
def test_get_stops_with_mock_data(mock_get_stops, mock_get_lines):
    mock_get_lines.return_value = ["Red"]

    mock_get_stops.return_value = [
        {
            "id": "place-alfcl",
            "attributes": {
                "name": "Alewife",
                "latitude": 42.395428,
                "longitude": -71.142483,
            },
        },
        {
            "id": "place-davis",
            "attributes": {
                "name": "Davis",
                "latitude": 42.39674,
                "longitude": -71.121815,
            },
        },
        {
            "id": "place-portr",
            "attributes": {
                "name": "Porter",
                "latitude": 42.3884,
                "longitude": -71.119149,
            },
        }
    ]

    response = client.get("/stops")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3
    assert any(stop["stop_name"] == "Alewife" for stop in data)
    assert all("coordinates" in stop for stop in data)
    assert all("lines" in stop for stop in data)
    assert all("adjacent_stops" in stop for stop in data)

    # Check that adjacency is mutual
    alewife = next((s for s in data if s["stop_name"] == "Alewife"), None)
    davis = next((s for s in data if s["stop_name"] == "Davis"), None)
    assert any(adj["stop_name"] == "Davis" for adj in alewife["adjacent_stops"])
    assert any(adj["stop_name"] == "Alewife" for adj in davis["adjacent_stops"])


# -------------------------------
# Edge Case: Empty subway lines
# -------------------------------
@patch("main.get_subway_lines", return_value=[])
def test_get_stops_empty_lines(mock_get_lines):
    response = client.get("/stops")
    assert response.status_code == 200
    assert response.json() == []


# -------------------------------
# Error Case: Broken stop data
# -------------------------------
@patch("main.get_subway_lines", return_value=["Red"])
@patch("main.get_subway_line_stops", side_effect=Exception("Test failure"))
def test_get_stops_failure_case(mock_get_stops, mock_get_lines):
    response = client.get("/stops")
    assert response.status_code == 500
    assert "Unexpected error" in response.json()["detail"]


# -------------------------------
# Test: Line and stop name mapping
# -------------------------------
@patch("main.get_subway_lines")
@patch("main.get_subway_line_stops")
def test_stop_id_and_name_mapping(mock_get_stops, mock_get_lines):
    mock_get_lines.return_value = ["Orange"]
    mock_get_stops.return_value = [
        {
            "id": "place-chncl",
            "attributes": {
                "name": "Chinatown",
                "latitude": 42.352547,
                "longitude": -71.062752,
            },
        },
        {
            "id": "place-dwnxg",
            "attributes": {
                "name": "Downtown Crossing",
                "latitude": 42.355518,
                "longitude": -71.060225,
            },
        }
    ]
    response = client.get("/stops")
    assert response.status_code == 200
    data = response.json()
    chinatown = next((s for s in data if s["stop_id"] == "place-chncl"), None)
    assert chinatown["stop_name"] == "Chinatown"
    assert "coordinates" in chinatown
    assert "lines" in chinatown
    assert isinstance(chinatown["lines"], list)


# -------------------------------
# Test: Adjacency directionality and isolation
# -------------------------------
@patch("main.get_subway_lines")
@patch("main.get_subway_line_stops")
def test_adjacency_mutuality(mock_get_stops, mock_get_lines):
    mock_get_lines.return_value = ["Blue"]
    mock_get_stops.return_value = [
        {
            "id": "place-state",
            "attributes": {
                "name": "State",
                "latitude": 42.358978,
                "longitude": -71.057598,
            },
        },
        {
            "id": "place-aqucl",
            "attributes": {
                "name": "Aquarium",
                "latitude": 42.359784,
                "longitude": -71.051652,
            },
        }
    ]
    response = client.get("/stops")
    data = response.json()
    state = next((s for s in data if s["stop_id"] == "place-state"), None)
    aquarium = next((s for s in data if s["stop_id"] == "place-aqucl"), None)

    assert any(adj["stop_id"] == "place-aqucl" for adj in state["adjacent_stops"])
    assert any(adj["stop_id"] == "place-state" for adj in aquarium["adjacent_stops"])


# -------------------------------
# Test: Coordinates must be valid float types
# -------------------------------
@patch("main.get_subway_lines")
@patch("main.get_subway_line_stops")
def test_coordinates_are_floats(mock_get_stops, mock_get_lines):
    mock_get_lines.return_value = ["Green"]
    mock_get_stops.return_value = [
        {
            "id": "place-hymnl",
            "attributes": {
                "name": "Haymarket",
                "latitude": 42.363021,
                "longitude": -71.05829,
            },
        }
    ]
    response = client.get("/stops")
    stop = response.json()[0]
    assert isinstance(stop["coordinates"]["latitude"], float)
    assert isinstance(stop["coordinates"]["longitude"], float)


# -------------------------------
# Corner Case: Duplicate stops on multiple lines
# -------------------------------
@patch("main.get_subway_lines")
@patch("main.get_subway_line_stops")
def test_duplicate_stops_across_lines(mock_get_stops, mock_get_lines):
    # Simulate stop appearing on two lines
    mock_get_lines.return_value = ["Red", "Orange"]

    shared_stop = {
        "id": "place-dwnxg",
        "attributes": {
            "name": "Downtown Crossing",
            "latitude": 42.355518,
            "longitude": -71.060225,
        }
    }

    mock_get_stops.side_effect = [
        [shared_stop],  # Red Line
        [shared_stop]   # Orange Line
    ]

    response = client.get("/stops")
    assert response.status_code == 200
    data = response.json()

    # There should only be one "Downtown Crossing"
    dtx_list = [stop for stop in data if stop["stop_id"] == "place-dwnxg"]
    assert len(dtx_list) == 1
    dtx = dtx_list[0]
    assert set(dtx["lines"]) == {"Red", "Orange"}

# -------------------------------
# Big Baseline Test. mock all stops for all lines after running main.py in GENERATE_MOCK_BASELINE_DATA=True mode
# compare result to golden_test_result.json
# note newly generated golden_test_result.json must be manually verified
# -------------------------------
@patch("main.get_subway_lines")
@patch("main.get_subway_line_stops")
def test_big_baseline_test(mock_get_stops, mock_get_lines):
    
    with open("get_subway_lines_mock_data.json", "r") as f:
        mock_get_lines.return_value = json.load(f)

    # Define custom logic based on the subway_line argument
    def mock_stops_for_line(subway_line):
        with open(f"get_subway_line_stops_mock_data_for_{subway_line}.json", "r") as f:
            stops_data = json.load(f)
        return stops_data

    mock_get_stops.side_effect = mock_stops_for_line

    response = client.get("/stops")
    assert response.status_code == 200
    data = response.json()
    with open(f"golden_test_result.json", "r") as f:
            golden_data = json.load(f)
    diff = DeepDiff(data, golden_data, ignore_order=True)
    assert diff == {}, f"Differences found:\n{diff}"


