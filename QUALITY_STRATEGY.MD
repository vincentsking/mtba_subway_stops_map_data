
# QUALITY_STRATEGY.MD

## Objectives

The goal of this project is to build a robust, testable, and maintainable API that exposes structured MBTA subway stop data, including coordinates, line mappings, and adjacent stop relationships. Quality is defined by correctness, reliability, clarity, and ease of extension.

---

## Scope

This quality strategy applies to:
- API endpoint logic, data parsing, and transformation
- Integration with the MBTA public API
- Internal data models and response structures
- Developer documentation and CI readiness

Out of scope:
- UI/frontend rendering
- High-performance caching or persistence layers
- Real-time streaming updates from MBTA

---

## Testing

### Unit Tests
- Mocked MBTA responses using `requests-mock` or `unittest.mock`
- Focused on:
  - Parsing and transformation logic
  - Adjacency calculations
  - Error handling for missing or malformed data

### Running the tests 
example output
```
> pytest test_main.py -vv
=============================================================================================== test session starts ================================================================================================
platform darwin -- Python 3.12.11, pytest-8.4.1, pluggy-1.6.0 -- python3.12
cachedir: .pytest_cache
rootdir: /Users/vincent.s.king/Development/mtba_subway_stops_map_data
plugins: anyio-4.9.0
collected 10 items                                                                                                                                                                                                 
test_main.py::test_make_a_request_success PASSED                                                                                                                                                             [ 10%]
test_main.py::test_make_a_request_429_retry PASSED                                                                                                                                                           [ 20%]
test_main.py::test_get_stops_with_mock_data PASSED                                                                                                                                                           [ 30%]
test_main.py::test_get_stops_empty_lines PASSED                                                                                                                                                              [ 40%]
test_main.py::test_get_stops_failure_case PASSED                                                                                                                                                             [ 50%]
test_main.py::test_stop_id_and_name_mapping PASSED                                                                                                                                                           [ 60%]
test_main.py::test_adjacency_mutuality PASSED                                                                                                                                                                [ 70%]
test_main.py::test_coordinates_are_floats PASSED                                                                                                                                                             [ 80%]
test_main.py::test_duplicate_stops_across_lines PASSED                                                                                                                                                       [ 90%]
test_main.py::test_big_baseline_test PASSED                                                                                                                                                                  [100%]

================================================================================================ 10 passed in 8.26s ================================================================================================
```
### Integration Tests
- Run API endpoints using `TestClient` from FastAPI
- Validate full response shape and content using known MBTA route IDs

### Edge Case Coverage
- Empty MBTA responses
- Duplicate stops on multiple lines
- Stops with no adjacent stations (ends of lines)

### Manual Verification for the Big Baseline Test
Here’s a cleaned-up and professional version for your **Quality Strategy** document section:

### Baseline Snapshot and Mocking Strategy

To ensure consistent and repeatable testing, I added a mechanism to run `main.py` in a **mock data generation mode** by setting:

```python
GENERATE_MOCK_BASELINE_DATA = True
```

When enabled, the application will:

* Write out `get_subway_lines_mock_data.json` — a snapshot of subway lines
* Write out a separate JSON file for each line's raw stop data, e.g.:

  * `get_subway_line_stops_mock_data_for_Red.json`
  * `get_subway_line_stops_mock_data_for_Orange.json`
  * ...and so on

After generating this data, I manually verified the application’s `/stops` output and saved a known-good result as:

```
golden_test_result.json
```

This baseline acts as a **reference snapshot** of expected behavior. In the final test suite (`test_main.py`), a dedicated test called `test_big_baseline_test` loads all the mock data and compares the live application output to this golden result.

This approach allows for:

* High-confidence regression testing
* Isolated offline testing without calling the live MBTA API
* Easier debugging when API responses or logic change

- Sample outputs compared to real MBTA subway map
- Verified JSON response format and completeness

---

## Observability

- Logging of MBTA API fetch errors and failed requests
- Plans for:
  - Request timing metrics
  - Endpoint hit counts

---

## Release Process

- Local: Run via `uvicorn main:app --reload`
- Deployment: Compatible with containerization or Python-based deployment pipelines
- GitHub-hosted source code and docs
- Future improvements:
  - GitHub Actions CI pipeline with linting and tests
  - Auto-generated OpenAPI schema docs

---

## Stakeholders

- **Platform QA Engineers** – validating map-building tools and route logic
- **Developers** – using the API for downstream transit or mapping tools
- **Product teams** – verifying transit coverage and integration logic
- **Test Automation Engineers** – extending unit and integration test coverage
