from fastapi import FastAPI, HTTPException
import requests
from typing import List, Dict
from collections import defaultdict
import uvicorn
import json

app = FastAPI(title="MBTA Subway Stop API")

MBTA_BASE_URL = "https://api-v3.mbta.com"
SUBWAY_ROUTE_TYPES = "0,1"  # 0 = light rail, 1 = heavy rail

@app.get("/stops", summary="Get subway stops with coordinates, lines, and adjacent stops")
def get_subway_stops() -> List[Dict]:
    try:
        # Step 1: Get subway routes
        routes_resp = requests.get(f"{MBTA_BASE_URL}/routes?filter[type]={SUBWAY_ROUTE_TYPES}")
        routes_data = routes_resp.json().get("data", [])
        route_ids = [route["id"] for route in routes_data]

        stops = {}
        for route_id in route_ids:
            # Step 2: Get trips
            trips_resp = requests.get(f"{MBTA_BASE_URL}/trips?filter[route]={route_id}")
            trip_data = trips_resp.json().get("data", [])
            if not trip_data:
                continue

            trip_id = trip_data[0]["id"]

            # Step 3: Get stop sequence
            sched_resp = requests.get(f"{MBTA_BASE_URL}/schedules?filter[trip]={trip_id}&sort=stop_sequence")
            schedule_data = sched_resp.json().get("data", [])
            stop_sequence = [
                entry["relationships"]["stop"]["data"]["id"]
                for entry in schedule_data
                if entry.get("relationships", {}).get("stop", {}).get("data")
            ]

            for i, stop_id in enumerate(stop_sequence):
                if stop_id not in stops:
                    stop_resp = requests.get(f"{MBTA_BASE_URL}/stops/{stop_id}")
                    stop_data = stop_resp.json().get("data", {})
                    if not stop_data:
                        continue

                    stops[stop_id] = {
                        "stop_name": stop_data["attributes"]["name"],
                        "coordinates": {
                            "latitude": stop_data["attributes"]["latitude"],
                            "longitude": stop_data["attributes"]["longitude"],
                        },
                        "lines": set(),
                        "adjacent_stops": defaultdict(set)
                    }

                stops[stop_id]["lines"].add(route_id)

                if i > 0:
                    prev_stop_id = stop_sequence[i - 1]
                    stops[stop_id]["adjacent_stops"][prev_stop_id].add(route_id)
                    stops[prev_stop_id]["adjacent_stops"][stop_id].add(route_id)

        # Finalize results
        results = []
        for stop_id, stop in stops.items():
            results.append({
                "stop_name": stop["stop_name"],
                "coordinates": stop["coordinates"],
                "lines": list(stop["lines"]),
                "adjacent_stops": [
                    {"stop": adj_id, "lines": list(lines)}
                    for adj_id, lines in stop["adjacent_stops"].items()
                ]
            })

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
