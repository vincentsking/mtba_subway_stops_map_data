from fastapi import FastAPI, HTTPException
import requests
from typing import List, Dict
from collections import defaultdict
import uvicorn
import json
import time
import logging
import traceback

logging.basicConfig(
    level=logging.INFO,  # or INFO in production
    format='[%(asctime)s] %(levelname)s - %(message)s',
)
log = logging.getLogger(__name__)

app = FastAPI(title="MBTA Subway Stop Map Location Data API")

MBTA_BASE_URL = "https://api-v3.mbta.com"
SUBWAY_ROUTE_TYPES = "0,1"  # 0 = light rail, 1 = heavy rail
GENERATE_MOCK_BASELINE_DATA = False

def make_a_request(url):
    log.debug(f"making a request to {url}")
    time.sleep(2)
    response = requests.get(url)
    if response.status_code == 429:
        reset = int(response.headers.get("x-ratelimit-reset",0))
        wait = max(1, reset - int(time.time()))
        log.warning(f"Got a 429 in for {url}, Rate limit hit. Waiting {wait} seconds.")
        time.sleep(wait)
        return make_a_request(url)
    elif response.status_code == 200:
        log.debug(response)
        return response
    else:
        log.debug(f"make_a_request return is {response.status_code}")
        return response

def get_subway_lines(subway_types) -> []:
    try:
        routes_resp = make_a_request(f"{MBTA_BASE_URL}/routes?filter[type]={subway_types}")
        routes_data = routes_resp.json().get("data", [])
        subway_lines = [route["id"] for route in routes_data]
        log.info(f"get_subway_lines -> {subway_lines}")
        if GENERATE_MOCK_BASELINE_DATA:
            with open("get_subway_lines_mock_data.json", "w") as f:
                json.dump(subway_lines, f, indent=2, sort_keys=True)
        return subway_lines
    except Exception as e:
        log.error("Unexpected error:\n" + traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


def get_subway_line_stops(subway_line) -> []:
    try:
        get_stops_url = f"{MBTA_BASE_URL}/stops?filter[route]={subway_line}"
        stops_response = make_a_request(get_stops_url)
        stops_data = stops_response.json().get("data", [])
        if GENERATE_MOCK_BASELINE_DATA:
            with open(f"get_subway_line_stops_mock_data_for_{subway_line}.json", "w") as f:
                json.dump(stops_data, f, indent=2, sort_keys=True)
        return stops_data
    except Exception as e:
        log.error("Unexpected error:\n" + traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/stops", summary="Get MBTA subway stops with coordinates, lines, and adjacent stops")
def get_subway_stops() -> List[Dict]:
    try:
        # Get subway lines
        subway_lines = get_subway_lines(SUBWAY_ROUTE_TYPES)
        stops = {}
        for subway_line in subway_lines:
            stop_data_list =  get_subway_line_stops(subway_line)
            stop_sequence = [stop["id"] for stop in stop_data_list]
            log.info(f"subway_line: {subway_line} stop sequence -> {stop_sequence}")
            for i, stop_data in enumerate(stop_data_list):
                stop_id = stop_data["id"]
                if stop_id not in stops:
                    stops[stop_id] = {
                        "stop_name": stop_data["attributes"]["name"],
                        "stop_id": stop_data["id"],
                        "coordinates": {
                            "latitude": stop_data["attributes"]["latitude"],
                            "longitude": stop_data["attributes"]["longitude"],
                        },
                        "lines": set(),
                        "adjacent_stops": defaultdict(set)
                    }

                stops[stop_id]["lines"].add(subway_line)
                if i > 0:
                    prev_stop_id = stop_sequence[i - 1]
                    # Record adjacency both ways
                    stops[stop_id]["adjacent_stops"][prev_stop_id].add(subway_line)
                    stops[prev_stop_id]["adjacent_stops"][stop_id].add(subway_line)

        # Finalize results
        results = []
        for stop_id, stop in stops.items():
            results.append({
                "stop_name": stop["stop_name"],
                "stop_id": stop["stop_id"],
                "coordinates": stop["coordinates"],
                "lines": list(stop["lines"]),
                "adjacent_stops": [
                    {"stop_id": adj_id, "stop_name": stops[adj_id]["stop_name"], "lines": list(stops[adj_id]["lines"])}
                    for adj_id in stop["adjacent_stops"]
                ]
            })
        #log.info(json.dumps(results[0], indent=2))
        return results

    except Exception as e:
        log.error("Unexpected error:\n" + traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

