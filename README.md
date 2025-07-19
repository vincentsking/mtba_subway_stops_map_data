
# MBTA Subway Map Data API

This project provides a simple REST API that exposes subway stop data for the MBTA (Massachusetts Bay Transportation Authority). It returns GPS coordinates, associated subway lines, and adjacent stops for each station on the light and heavy rail network.

## Features

- Real-time data fetched from the MBTA public API
- Built using **FastAPI** for easy documentation and fast performance
- Exposes one endpoint: `/stops`
- Includes logic for calculating **adjacent stops** based on train stops
- JSON output includes:
  - Stop name
  - stop_id
  - Coordinates (latitude/longitude)
  - Subway lines
  - Adjacent stops and the lines they are connected by

## Installation

```bash
git clone https://github.com/your-username/mbta-subway-api.git
cd mbta-subway-api
pip install -r requirements.txt
python main.py
```

Then open your browser at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for the Swagger UI.

## Requirements

- Python 3.8+
- FastAPI
- Uvicorn
- Requests
- PyTest

Install dependencies:

```bash
pip install fastapi uvicorn requests json deepdiff
```

## API Endpoint

### `GET /stops`

Returns a list of MBTA subway stops with:
- Name
- Coordinates
- Lines (Red, Orange, Blue, Green)
- Adjacent stops and the lines connecting them

Example:
```json
{
    "stop_name": "Downtown Crossing",
    "stop_id": "place-dwnxg",
    "coordinates": {
      "latitude": 42.355518,
      "longitude": -71.060225
    },
    "lines": [
      "Orange",
      "Red"
    ],
    "adjacent_stops": [
      {
        "stop_id": "place-pktrm",
        "stop_name": "Park Street",
        "lines": [
          "Green-C",
          "Green-B",
          "Red",
          "Green-E",
          "Green-D"
        ]
      },
      {
        "stop_id": "place-sstat",
        "stop_name": "South Station",
        "lines": [
          "Red"
        ]
      },
      {
        "stop_id": "place-chncl",
        "stop_name": "Chinatown",
        "lines": [
          "Orange"
        ]
      },
      {
        "stop_id": "place-state",
        "stop_name": "State",
        "lines": [
          "Orange",
          "Blue"
        ]
      }
    ]
  }
```

## Design Decisions
### Notes on Development Approach

I initially gave this challenge to ChatGPT out of curiosity and to potentially accelerate the early stages of the project. Its example served as a decent starting point and did help get things off the ground quickly. The use of **Uvicorn** for hot-reloading was especially helpful during development — every time you save the file, the service restarts automatically, which made iterating fast and smooth.

At first glance, the results looked promising. However, as I dug deeper, several flaws became clear:

* **Limited coverage of subway lines**: The app only completed a small portion of one subway line. It turned out that the MBTA API was returning `429 Too Many Requests` responses after the rate limit was hit, but these were silently ignored. As a result, many stops were skipped without warning.

* **Insufficient error handling**: The original solution lacked robustness. There was no proper retry logic, and exceptions weren't caught or logged, making debugging difficult.

* **Lack of modularity and reuse**: The code structure made it difficult to test individual components or adapt the logic without heavy duplication.

* **Missing logging**: Iterating without debug logs slowed down progress. I added much more granular logging to help visualize what the app was doing at each step.

To address these issues, I created a generic `make_a_request(url)` function that wraps `requests.get()` and checks for valid return codes. If a `429` is received, it extracts the `x-ratelimit-reset` value from the headers, waits the required amount of time, and retries the request.

I also discovered that both the **Red Line** and **Mattapan Line** lacked proper `stop_sequence` values from the `/schedules` endpoint. After some research, I found this is a known issue with the MBTA API — likely stemming from their backend data, not the API layer itself.

The original approach attempted to derive stop sequences by pulling trip schedules and sorting them by `stop_sequence`, which made sense in theory. However, in practice, the stop IDs retrieved from the `relationships.stop.data.id` field in the schedule API **did not match** the IDs returned from the `/stops` API. This mismatch caused major problems with the `adjacent_stops` logic and led to duplicated stops that didn’t include all expected lines.

For reference, I kept ChatGPT's original code in the repo under `ai_orig.py`, but ended up scrapping most of it in favor of a more simple, reliable and testable solution.


##  Limitations
- No persistent cache or database; queries MBTA API on each call


## Future Improvements

- Add persistent caching or DB backend
- CI pipeline with GitHub Actions
- Add filtering/query params to the endpoint

## 📄 License

MIT (or specify another)
