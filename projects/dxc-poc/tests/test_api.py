from __future__ import annotations

import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", message="Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.")

from starlette.testclient import TestClient

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from backend.app import app


def _client() -> TestClient:
    return TestClient(app)


def test_health_reports_ready_state() -> None:
    with _client() as client:
        response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["db_loaded"] is True
    assert payload["models_loaded"] == ["prophet", "nbeats", "lstm"]


def test_queue_endpoints_cover_both_security_areas() -> None:
    with _client() as client:
        current = client.get("/queues/current")
        tsa_forecast = client.get("/queues/forecast", params={"airport": "ATL"})
        precheck_forecast = client.get(
            "/queues/forecast",
            params={"airport": "ATL", "area": "SECURITY_PRECHECK"},
        )

    assert current.status_code == 200
    queues = current.json()["queues"]
    assert any(item["area_type"] == "SECURITY_TSA" for item in queues)
    assert any(item["area_type"] == "SECURITY_PRECHECK" for item in queues)

    assert tsa_forecast.status_code == 200
    assert tsa_forecast.json()["points"]

    assert precheck_forecast.status_code == 200
    assert precheck_forecast.json()["points"]


def test_clock_update_round_trip() -> None:
    with _client() as client:
        before = client.get("/config/clock")
        assert before.status_code == 200
        original_demo_now = before.json()["demo_now"]

        updated = client.post("/config/clock", json={"demo_now": "2022-07-04T07:00:00"})
        restored = client.post("/config/clock", json={"demo_now": original_demo_now})

    assert updated.status_code == 200
    assert updated.json()["demo_now"] == "2022-07-04T07:00:00"
    assert restored.status_code == 200
    assert restored.json()["demo_now"] == original_demo_now


def test_staffing_simulation_and_kpis() -> None:
    with _client() as client:
        staffing = client.get(
            "/staffing/recommend",
            params={"airport": "ATL", "date": "2021-11-24"},
        )
        simulation = client.post(
            "/simulate/what-if",
            json={
                "airport_code": "ATL",
                "area_type": "SECURITY_TSA",
                "use_current_arrivals": True,
                "arrival_rate_per_min": None,
                "num_lanes": 6,
                "precheck_ratio": 0.2,
                "service_rate_per_lane": 3.0,
                "surge_multiplier": 1.0,
                "duration_min": 60,
            },
        )
        kpis = client.get(
            "/dashboard/kpis",
            params={"date_from": "2021-11-20", "date_to": "2021-11-24"},
        )

    assert staffing.status_code == 200
    staffing_payload = staffing.json()
    assert staffing_payload["hours"]
    assert staffing_payload["totals"]["peak_lanes"] >= 0

    assert simulation.status_code == 200
    simulation_payload = simulation.json()
    assert simulation_payload["baseline"]["num_lanes"] > 0
    assert simulation_payload["scenario"]["num_lanes"] == 6

    assert kpis.status_code == 200
    kpi_payload = kpis.json()
    assert kpi_payload["trend"]
    assert kpi_payload["kpis"]["total_pax"] > 0
