
# 🧪 QUALITY_STRATEGY.MD

## 📌 Objectives

The goal of this project is to build a robust, testable, and maintainable API that exposes structured MBTA subway stop data, including coordinates, line mappings, and adjacent stop relationships. Quality is defined by correctness, reliability, clarity, and ease of extension.

---

## 🧭 Scope

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

## 🧪 Testing

### ✅ Unit Tests
- Mocked MBTA responses using `requests-mock` or `unittest.mock`
- Focused on:
  - Parsing and transformation logic
  - Adjacency calculations
  - Error handling for missing or malformed data

### ✅ Integration Tests
- Run API endpoints using `TestClient` from FastAPI
- Validate full response shape and content using known MBTA route IDs

### ✅ Edge Case Coverage
- Empty MBTA responses
- Duplicate stops on multiple lines
- Stops with no adjacent stations (ends of lines)

### ✅ Manual Verification
- Sample outputs compared to real MBTA subway map
- Verified JSON response format and completeness

---

## 🔍 Observability

- Logging of MBTA API fetch errors and failed requests
- Plans for:
  - Request timing metrics
  - Endpoint hit counts
  - Future integration with Prometheus/Grafana

---

## 🚀 Release Process

- Local: Run via `uvicorn main:app --reload`
- Deployment: Compatible with containerization or Python-based deployment pipelines
- GitHub-hosted source code and docs
- Future improvements:
  - GitHub Actions CI pipeline with linting and tests
  - Auto-generated OpenAPI schema docs

---

## 👥 Stakeholders

- **Platform QA Engineers** – validating map-building tools and route logic
- **Developers** – using the API for downstream transit or mapping tools
- **Product teams** – verifying transit coverage and integration logic
- **Test Automation Engineers** – extending unit and integration test coverage
