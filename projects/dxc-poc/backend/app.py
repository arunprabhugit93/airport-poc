"""FastAPI app for the DXC Airport Queue Management POC."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date, datetime, time, timedelta
from pathlib import Path

import duckdb
import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from backend import config
from backend.models.queue_math import min_lanes_for_sla, mm_c_wait
from backend.sim.checkpoint_sim import SimulationResult, simulate_checkpoint

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PACKAGE_ROOT / "data" / config.DUCKDB_FILENAME
MODELS_DIR = PACKAGE_ROOT / "data" / "models"

TREND_UP_EPSILON = 0.25
TREND_DOWN_EPSILON = -0.25


class HealthResponse(BaseModel):
    status: str
    db_loaded: bool
    models_loaded: list[str]
    demo_now: datetime


class CurrentQueue(BaseModel):
    airport_code: str
    area_type: str
    pax_last_hour: int
    lanes_open: int
    wait_min: float
    sla_status: str
    predicted_breach_in_min: int | None
    trend: str


class CurrentQueuesResponse(BaseModel):
    as_of: datetime
    queues: list[CurrentQueue]


class AirportStatus(BaseModel):
    airport_code: str
    name: str
    lat: float
    lon: float
    worst_wait_min: float
    sla_status: str
    active_anomalies: int
    total_pax_today: int


class AirportsResponse(BaseModel):
    as_of: datetime
    airports: list[AirportStatus]


class ForecastPoint(BaseModel):
    target_ts: datetime
    horizon_min: int
    pred_wait_min: float
    pred_throughput: int | None
    lower_min: float | None
    upper_min: float | None


class ForecastResponse(BaseModel):
    airport_code: str
    area_type: str
    model_name: str
    origin_ts: datetime
    horizon_min: int
    points: list[ForecastPoint]


class AnomalyEvent(BaseModel):
    event_id: int
    airport_code: str
    area_type: str | None
    detected_at: datetime
    anomaly_type: str
    detector: str
    metric: str
    observed_value: float
    expected_value: float | None
    score: float
    severity: str
    description: str | None


class RecentAnomaliesResponse(BaseModel):
    as_of: datetime
    window_hours: int
    events: list[AnomalyEvent]


class StaffingHour(BaseModel):
    rec_hour: int
    forecast_pax: int
    recommended_lanes: int
    recommended_staff: int
    expected_wait_min: float
    sla_met: bool


class StaffingTotals(BaseModel):
    peak_lanes: int
    total_staff_hours: int


class StaffingResponse(BaseModel):
    airport_code: str
    rec_date: date
    area_type: str
    sla_target_min: float
    hours: list[StaffingHour]
    totals: StaffingTotals


class ScenarioMetrics(BaseModel):
    num_lanes: int
    precheck_ratio: float
    mean_wait_min: float
    p95_wait_min: float
    max_queue_len: int
    lane_utilisation: float
    sla_breach_min: int
    sla_target_min: float


class ScenarioDelta(BaseModel):
    mean_wait_min: float
    sla_breach_min: int


class WhatIfRequest(BaseModel):
    airport_code: str
    area_type: str
    use_current_arrivals: bool = True
    arrival_rate_per_min: float | None = None
    num_lanes: int = Field(ge=1, le=20)
    precheck_ratio: float = Field(ge=0.0, le=1.0)
    service_rate_per_lane: float = Field(gt=0.0)
    surge_multiplier: float = Field(default=1.0, gt=0.0)
    duration_min: int = Field(default=60, ge=1, le=240)


class WhatIfResponse(BaseModel):
    scenario: ScenarioMetrics
    baseline: ScenarioMetrics
    delta: ScenarioDelta


class KpiSummary(BaseModel):
    avg_wait_min: float
    p95_wait_min: float
    total_pax: int
    sla_breach_rate: float
    anomaly_count: int
    busiest_airport: str | None
    busiest_hour: int | None


class KpiTrendPoint(BaseModel):
    obs_date: date
    avg_wait_min: float
    total_pax: int
    sla_breach_rate: float


class KpisResponse(BaseModel):
    airport_code: str
    date_from: date
    date_to: date
    kpis: KpiSummary
    trend: list[KpiTrendPoint]


class ModelDescriptor(BaseModel):
    name: str
    label: str
    default: bool
    horizon_max_min: int


class ModelsResponse(BaseModel):
    models: list[ModelDescriptor]


class AllAreaQueue(BaseModel):
    airport_code: str
    area_type: str
    queue_length: int
    wait_min: float
    staff_on_duty: int
    sla_status: str


class AllAreaQueuesResponse(BaseModel):
    as_of: datetime
    queues: list[AllAreaQueue]


class JourneyStage(BaseModel):
    stage: str
    avg_wait_min: float
    queue_length: int
    status: str


class PassengerJourneyResponse(BaseModel):
    airport_code: str
    as_of: datetime
    stages: list[JourneyStage]
    total_journey_min: float
    bottleneck: str


class Recommendation(BaseModel):
    priority: str
    airport_code: str
    area: str
    action: str
    reason: str
    impact: str


class RecommendationsResponse(BaseModel):
    as_of: datetime
    recommendations: list[Recommendation]


class HeatmapCell(BaseModel):
    day_of_week: int
    hour: int
    avg_wait_min: float
    avg_pax: float


class HeatmapResponse(BaseModel):
    airport_code: str
    area_type: str
    cells: list[HeatmapCell]


class ClockResponse(BaseModel):
    demo_now: datetime
    min: datetime
    max: datetime


class ClockUpdateRequest(BaseModel):
    demo_now: datetime


class BackendStore:
    def __init__(self, db_path: Path, models_dir: Path) -> None:
        self.db_path = db_path
        self.models_dir = models_dir
        self.demo_now = config.DEMO_NOW
        self.min_demo_now: datetime | None = None
        self.max_demo_now: datetime | None = None
        self.models_loaded: list[str] = []
        self.refresh()

    def refresh(self) -> None:
        self.models_loaded = [
            name
            for name in config.MODEL_NAMES
            if any(self.models_dir.glob(f"{name}_*.pkl"))
        ]
        if not self.db_path.exists():
            self.min_demo_now = None
            self.max_demo_now = None
            return

        with self.connect() as con:
            min_date, max_date = con.execute(
                """
                SELECT MIN(obs_date), MAX(obs_date)
                FROM tsa_throughput
                WHERE grain = 'daily'
                """
            ).fetchone()
        if min_date is None or max_date is None:
            self.min_demo_now = None
            self.max_demo_now = None
            return

        self.min_demo_now = datetime.combine(min_date, time(0, 0))
        self.max_demo_now = datetime.combine(max_date, time(23, 0))
        if self.demo_now < self.min_demo_now:
            self.demo_now = self.min_demo_now
        if self.demo_now > self.max_demo_now:
            self.demo_now = self.max_demo_now

    def connect(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(str(self.db_path), read_only=True)

    @property
    def db_loaded(self) -> bool:
        return self.db_path.exists() and self.min_demo_now is not None and self.max_demo_now is not None


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.store = BackendStore(DB_PATH, MODELS_DIR)
    yield


app = FastAPI(
    title="DXC Airport Queue Management POC API",
    version="0.1.0",
    lifespan=lifespan,
)


def _store() -> BackendStore:
    if not hasattr(app.state, "store"):
        app.state.store = BackendStore(DB_PATH, MODELS_DIR)
    return app.state.store


def _validate_airport(airport: str) -> str:
    if airport not in config.AIRPORT_CODES and airport != "ALL":
        raise HTTPException(status_code=404, detail=f"Unknown airport '{airport}'")
    return airport


def _validate_area(area: str, *, security_only: bool = False) -> str:
    valid = config.SECURITY_AREAS if security_only else config.AREA_TYPES
    if area not in valid:
        raise HTTPException(status_code=422, detail=f"Unknown area_type '{area}'")
    return area


def _validate_model(model: str) -> str:
    if model not in config.MODEL_NAMES:
        raise HTTPException(status_code=422, detail=f"Unknown model '{model}'")
    return model


def _ensure_ready(store: BackendStore) -> None:
    if not store.db_loaded:
        raise HTTPException(status_code=503, detail="DuckDB is not loaded")


def _current_ts(store: BackendStore) -> datetime:
    return store.demo_now


def _current_origin(store: BackendStore) -> datetime:
    now = _current_ts(store)
    return now.replace(minute=0, second=0, microsecond=0)


def _hour_parts(ts: datetime) -> tuple[date, int]:
    return ts.date(), ts.hour


def _sla_status(wait_min: float) -> str:
    if wait_min >= config.BREACH_WAIT_MIN:
        return "BREACH"
    if wait_min >= config.WARN_WAIT_MIN:
        return "WARNING"
    return "OK"


def _trend_label(current_wait: float, previous_wait: float | None) -> str:
    if previous_wait is None:
        return "FLAT"
    delta = current_wait - previous_wait
    if delta >= TREND_UP_EPSILON:
        return "UP"
    if delta <= TREND_DOWN_EPSILON:
        return "DOWN"
    return "FLAT"


def _forecast_origin(
    con: duckdb.DuckDBPyConnection,
    airport: str,
    area: str,
    model: str,
    target_origin: datetime,
) -> datetime | None:
    rows = con.execute(
        """
        SELECT DISTINCT origin_ts
        FROM queue_predictions
        WHERE airport_code = ? AND area_type = ? AND model_name = ?
        ORDER BY origin_ts
        """,
        [airport, area, model],
    ).fetchall()
    if not rows:
        return None

    origins = [row[0] for row in rows]
    return min(
        origins,
        key=lambda value: (abs(value - target_origin), value > target_origin, value),
    )


def _forecast_points(
    con: duckdb.DuckDBPyConnection,
    airport: str,
    area: str,
    model: str,
    target_origin: datetime,
    horizon: int,
) -> tuple[datetime, list[ForecastPoint]]:
    origin = _forecast_origin(con, airport, area, model, target_origin)
    if origin is None:
        raise HTTPException(status_code=404, detail="No forecast rows available")

    rows = con.execute(
        """
        SELECT target_ts, horizon_min, pred_wait_min, pred_throughput, lower_min, upper_min
        FROM queue_predictions
        WHERE airport_code = ?
          AND area_type = ?
          AND model_name = ?
          AND origin_ts = ?
          AND horizon_min <= ?
        ORDER BY horizon_min
        """,
        [airport, area, model, origin, horizon],
    ).fetchall()
    return origin, [
        ForecastPoint(
            target_ts=row[0],
            horizon_min=row[1],
            pred_wait_min=round(float(row[2]), 3),
            pred_throughput=row[3],
            lower_min=None if row[4] is None else round(float(row[4]), 3),
            upper_min=None if row[5] is None else round(float(row[5]), 3),
        )
        for row in rows
    ]


def _current_security_rows(
    con: duckdb.DuckDBPyConnection,
    ts: datetime,
    airport: str | None = None,
) -> pd.DataFrame:
    obs_date, obs_hour = _hour_parts(ts)
    sql = """
        SELECT airport_code, area_type, pax, lanes_open, wait_min_est
        FROM tsa_throughput
        WHERE grain = 'checkpoint_hour'
          AND obs_date = ?
          AND obs_hour = ?
    """
    params: list[object] = [obs_date, obs_hour]
    if airport:
        sql += " AND airport_code = ?"
        params.append(airport)
    sql += " ORDER BY airport_code, area_type"
    return con.execute(sql, params).fetchdf()


def _previous_wait_lookup(
    con: duckdb.DuckDBPyConnection,
    ts: datetime,
    airport: str | None = None,
) -> dict[tuple[str, str], float]:
    previous = ts - timedelta(hours=1)
    obs_date, obs_hour = _hour_parts(previous)
    sql = """
        SELECT airport_code, area_type, wait_min_est
        FROM tsa_throughput
        WHERE grain = 'checkpoint_hour'
          AND obs_date = ?
          AND obs_hour = ?
    """
    params: list[object] = [obs_date, obs_hour]
    if airport:
        sql += " AND airport_code = ?"
        params.append(airport)
    rows = con.execute(sql, params).fetchall()
    return {(row[0], row[1]): float(row[2]) for row in rows}


def _predicted_breach_minutes(
    con: duckdb.DuckDBPyConnection,
    airport: str,
    area: str,
    current_wait: float,
    target_origin: datetime,
) -> int | None:
    if current_wait >= config.BREACH_WAIT_MIN:
        return 0

    try:
        _, points = _forecast_points(
            con,
            airport=airport,
            area=area,
            model="prophet",
            target_origin=target_origin,
            horizon=180,
        )
    except HTTPException as exc:
        if exc.status_code == 404:
            return None
        raise
    for point in points:
        if point.pred_wait_min >= config.BREACH_WAIT_MIN:
            return point.horizon_min
    return None


def _scenario_metrics(
    result: SimulationResult,
    *,
    num_lanes: int,
    precheck_ratio: float,
) -> ScenarioMetrics:
    return ScenarioMetrics(
        num_lanes=num_lanes,
        precheck_ratio=round(precheck_ratio, 3),
        mean_wait_min=result.mean_wait_min,
        p95_wait_min=result.p95_wait_min,
        max_queue_len=result.max_queue_len,
        lane_utilisation=result.lane_utilisation,
        sla_breach_min=result.sla_breach_min,
        sla_target_min=config.SLA_TARGET_MIN,
    )


@app.get("/health", response_model=HealthResponse)
def health(response: Response) -> HealthResponse:
    store = _store()
    ready = store.db_loaded and bool(store.models_loaded)
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(
        status="ok" if ready else "degraded",
        db_loaded=store.db_loaded,
        models_loaded=store.models_loaded,
        demo_now=_current_ts(store),
    )


@app.get("/airports", response_model=AirportsResponse)
def airports() -> AirportsResponse:
    store = _store()
    _ensure_ready(store)
    as_of = _current_ts(store)

    with store.connect() as con:
        current = _current_security_rows(con, as_of)
        if current.empty:
            return AirportsResponse(as_of=as_of, airports=[])

        airport_ref = con.execute(
            """
            SELECT airport_code, name, lat, lon
            FROM airports_ref
            ORDER BY airport_code
            """
        ).fetchdf()
        pax_today = con.execute(
            """
            SELECT airport_code, pax
            FROM tsa_throughput
            WHERE grain = 'daily' AND obs_date = ?
            """,
            [as_of.date()],
        ).fetchdf()
        anomalies = con.execute(
            """
            SELECT airport_code, COUNT(*) AS active_anomalies
            FROM anomaly_events
            WHERE detected_at BETWEEN ? AND ?
              AND airport_code <> 'ALL'
            GROUP BY airport_code
            """,
            [as_of - timedelta(hours=24), as_of],
        ).fetchdf()

    grouped = (
        current.groupby("airport_code")
        .agg(worst_wait_min=("wait_min_est", "max"))
        .reset_index()
    )
    merged = airport_ref.merge(grouped, on="airport_code", how="left")
    merged = merged.merge(pax_today, on="airport_code", how="left")
    merged = merged.merge(anomalies, on="airport_code", how="left")
    merged = merged.fillna({"worst_wait_min": 0.0, "pax": 0, "active_anomalies": 0})

    airports_payload = [
        AirportStatus(
            airport_code=row["airport_code"],
            name=row["name"],
            lat=float(row["lat"]),
            lon=float(row["lon"]),
            worst_wait_min=round(float(row["worst_wait_min"]), 3),
            sla_status=_sla_status(float(row["worst_wait_min"])),
            active_anomalies=int(row["active_anomalies"]),
            total_pax_today=int(row["pax"]),
        )
        for _, row in merged.iterrows()
    ]
    return AirportsResponse(as_of=as_of, airports=airports_payload)


@app.get("/queues/current", response_model=CurrentQueuesResponse)
def queues_current(airport: str | None = None) -> CurrentQueuesResponse:
    if airport is not None:
        _validate_airport(airport)

    store = _store()
    _ensure_ready(store)
    as_of = _current_ts(store)
    target_origin = _current_origin(store)

    with store.connect() as con:
        current = _current_security_rows(con, as_of, airport)
        previous_waits = _previous_wait_lookup(con, as_of, airport)

        queues = [
            CurrentQueue(
                airport_code=row["airport_code"],
                area_type=row["area_type"],
                pax_last_hour=int(row["pax"]),
                lanes_open=int(row["lanes_open"]),
                wait_min=round(float(row["wait_min_est"]), 3),
                sla_status=_sla_status(float(row["wait_min_est"])),
                predicted_breach_in_min=_predicted_breach_minutes(
                    con,
                    airport=row["airport_code"],
                    area=row["area_type"],
                    current_wait=float(row["wait_min_est"]),
                    target_origin=target_origin,
                ),
                trend=_trend_label(
                    float(row["wait_min_est"]),
                    previous_waits.get((row["airport_code"], row["area_type"])),
                ),
            )
            for _, row in current.iterrows()
        ]

    return CurrentQueuesResponse(as_of=as_of, queues=queues)


@app.get("/queues/all-areas", response_model=AllAreaQueuesResponse)
def queues_all_areas(airport: str | None = None) -> AllAreaQueuesResponse:
    """Current queue state for ALL area types (security + ops areas)."""
    if airport is not None:
        _validate_airport(airport)

    store = _store()
    _ensure_ready(store)
    as_of = _current_ts(store)

    queues: list[AllAreaQueue] = []

    with store.connect() as con:
        # Security areas from tsa_throughput
        security = _current_security_rows(con, as_of, airport)
        for _, row in security.iterrows():
            queues.append(
                AllAreaQueue(
                    airport_code=row["airport_code"],
                    area_type=row["area_type"],
                    queue_length=int(row["pax"]),
                    wait_min=round(float(row["wait_min_est"]), 1),
                    staff_on_duty=int(row["lanes_open"]) * config.OFFICERS_PER_LANE,
                    sla_status=_sla_status(float(row["wait_min_est"])),
                )
            )

        # Ops areas from airport_ops (CHECKIN, GATE, BAGGAGE, IMMIGRATION)
        obs_date, obs_hour = _hour_parts(as_of)
        ops_sql = """
            SELECT airport_code, area_type, queue_length, wait_min, staff_on_duty
            FROM airport_ops
            WHERE CAST(ts AS DATE) = ?
              AND EXTRACT(HOUR FROM ts) = ?
        """
        ops_params: list[object] = [obs_date, obs_hour]
        if airport:
            ops_sql += " AND airport_code = ?"
            ops_params.append(airport)
        ops_sql += " ORDER BY airport_code, area_type"
        ops_rows = con.execute(ops_sql, ops_params).fetchall()

        for row in ops_rows:
            queues.append(
                AllAreaQueue(
                    airport_code=row[0],
                    area_type=row[1],
                    queue_length=int(row[2]) if row[2] is not None else 0,
                    wait_min=round(float(row[3]), 1) if row[3] is not None else 0.0,
                    staff_on_duty=int(row[4]) if row[4] is not None else 0,
                    sla_status=_sla_status(float(row[3])) if row[3] is not None else "OK",
                )
            )

    return AllAreaQueuesResponse(as_of=as_of, queues=queues)


@app.get("/passenger-journey", response_model=PassengerJourneyResponse)
def passenger_journey(airport: str) -> PassengerJourneyResponse:
    """Estimated time through each stage for a passenger at a given airport."""
    _validate_airport(airport)

    store = _store()
    _ensure_ready(store)
    as_of = _current_ts(store)

    stages: list[JourneyStage] = []
    stage_order = ["CHECKIN", "SECURITY_TSA", "IMMIGRATION", "GATE", "BAGGAGE"]

    with store.connect() as con:
        obs_date, obs_hour = _hour_parts(as_of)

        # Security data
        security = _current_security_rows(con, as_of, airport)
        security_lookup: dict[str, tuple[float, int]] = {}
        for _, row in security.iterrows():
            security_lookup[row["area_type"]] = (
                float(row["wait_min_est"]),
                int(row["pax"]),
            )

        # Ops data
        ops_rows = con.execute(
            """
            SELECT area_type, wait_min, queue_length
            FROM airport_ops
            WHERE airport_code = ?
              AND CAST(ts AS DATE) = ?
              AND EXTRACT(HOUR FROM ts) = ?
            """,
            [airport, obs_date, obs_hour],
        ).fetchall()
        ops_lookup: dict[str, tuple[float, int]] = {
            row[0]: (float(row[1]) if row[1] else 0.0, int(row[2]) if row[2] else 0)
            for row in ops_rows
        }

    for stage_name in stage_order:
        if stage_name in config.SECURITY_AREAS:
            if stage_name in security_lookup:
                wait, queue = security_lookup[stage_name]
            else:
                wait, queue = 0.0, 0
        else:
            if stage_name in ops_lookup:
                wait, queue = ops_lookup[stage_name]
            else:
                wait, queue = 0.0, 0
        stages.append(
            JourneyStage(
                stage=stage_name,
                avg_wait_min=round(wait, 1),
                queue_length=queue,
                status=_sla_status(wait),
            )
        )

    total_journey = sum(s.avg_wait_min for s in stages)
    bottleneck = max(stages, key=lambda s: s.avg_wait_min).stage if stages else "UNKNOWN"

    return PassengerJourneyResponse(
        airport_code=airport,
        as_of=as_of,
        stages=stages,
        total_journey_min=round(total_journey, 1),
        bottleneck=bottleneck,
    )


@app.get("/operations/recommendations", response_model=RecommendationsResponse)
def operations_recommendations(airport: str | None = None) -> RecommendationsResponse:
    """Actionable ops recommendations based on current queue state."""
    if airport is not None:
        _validate_airport(airport)

    store = _store()
    _ensure_ready(store)
    as_of = _current_ts(store)

    recommendations: list[Recommendation] = []

    with store.connect() as con:
        obs_date, obs_hour = _hour_parts(as_of)

        # Check security areas for breaches
        security = _current_security_rows(con, as_of, airport)
        for _, row in security.iterrows():
            code = row["airport_code"]
            area = row["area_type"]
            wait = float(row["wait_min_est"])
            pax = int(row["pax"])
            lanes = int(row["lanes_open"])

            if wait >= config.BREACH_WAIT_MIN:
                service_rate = config.SERVICE_RATE_PER_LANE.get(area, 3.0)
                # Estimate lanes needed to get below SLA
                needed_lanes = lanes
                while needed_lanes < 20:
                    needed_lanes += 1
                    est_wait = mm_c_wait(pax / 60.0, service_rate, needed_lanes)
                    if est_wait < config.SLA_TARGET_MIN:
                        break
                extra = needed_lanes - lanes
                est_reduced = mm_c_wait(pax / 60.0, service_rate, needed_lanes)
                recommendations.append(
                    Recommendation(
                        priority="HIGH",
                        airport_code=code,
                        area=area,
                        action=f"Open {extra} additional lane{'s' if extra != 1 else ''}",
                        reason=f"Wait time {wait:.1f} min exceeds SLA ({config.SLA_TARGET_MIN:.0f} min), {pax} pax/hr with only {lanes} lanes",
                        impact=f"Estimated wait reduction to {est_reduced:.1f} min",
                    )
                )
            elif wait >= config.WARN_WAIT_MIN:
                recommendations.append(
                    Recommendation(
                        priority="MEDIUM",
                        airport_code=code,
                        area=area,
                        action="Prepare additional lane for activation",
                        reason=f"Wait time {wait:.1f} min approaching SLA threshold ({config.SLA_TARGET_MIN:.0f} min)",
                        impact="Prevent potential SLA breach in next 15-30 min",
                    )
                )

        # Check ops areas for high waits
        ops_sql = """
            SELECT airport_code, area_type, queue_length, wait_min, staff_on_duty
            FROM airport_ops
            WHERE CAST(ts AS DATE) = ?
              AND EXTRACT(HOUR FROM ts) = ?
        """
        ops_params: list[object] = [obs_date, obs_hour]
        if airport:
            ops_sql += " AND airport_code = ?"
            ops_params.append(airport)
        ops_rows = con.execute(ops_sql, ops_params).fetchall()

        for row in ops_rows:
            code, area, queue_len, wait, staff = row[0], row[1], row[2], row[3], row[4]
            if wait is None:
                continue
            wait = float(wait)
            if wait >= config.BREACH_WAIT_MIN:
                recommendations.append(
                    Recommendation(
                        priority="HIGH",
                        airport_code=code,
                        area=area,
                        action=f"Add staff to {area.lower().replace('_', ' ')} area",
                        reason=f"Wait time {wait:.1f} min exceeds SLA, queue length {queue_len}, staff on duty {staff}",
                        impact=f"Reduce queue from {queue_len} and bring wait below {config.SLA_TARGET_MIN:.0f} min",
                    )
                )
            elif wait >= config.WARN_WAIT_MIN:
                recommendations.append(
                    Recommendation(
                        priority="MEDIUM",
                        airport_code=code,
                        area=area,
                        action=f"Monitor {area.lower().replace('_', ' ')} staffing levels",
                        reason=f"Wait time {wait:.1f} min approaching SLA threshold, {staff} staff on duty",
                        impact="Prevent potential SLA breach",
                    )
                )

        # Check for recent anomalies
        anomalies_sql = """
            SELECT airport_code, area_type, anomaly_type, severity, description
            FROM anomaly_events
            WHERE detected_at BETWEEN ? AND ?
        """
        anomaly_params: list[object] = [as_of - timedelta(hours=6), as_of]
        if airport:
            anomalies_sql += " AND airport_code = ?"
            anomaly_params.append(airport)
        anomalies_sql += " AND severity IN ('HIGH', 'MEDIUM') ORDER BY detected_at DESC LIMIT 10"
        anomaly_rows = con.execute(anomalies_sql, anomaly_params).fetchall()

        for row in anomaly_rows:
            a_code, a_area, a_type, a_severity, a_desc = row
            if a_code == "ALL":
                continue
            recommendations.append(
                Recommendation(
                    priority=a_severity,
                    airport_code=a_code,
                    area=a_area or "ALL",
                    action=f"Investigate {a_type.lower()} anomaly",
                    reason=a_desc or f"{a_type} detected at {a_area or 'system-wide'}",
                    impact="Early intervention prevents cascading delays",
                )
            )

    # Sort: HIGH first, then MEDIUM, then LOW
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    recommendations.sort(key=lambda r: priority_order.get(r.priority, 3))

    return RecommendationsResponse(as_of=as_of, recommendations=recommendations)


@app.get("/queues/heatmap", response_model=HeatmapResponse)
def queues_heatmap(
    airport: str,
    area: str = "SECURITY_TSA",
    days: int = Query(default=30, ge=1, le=365),
) -> HeatmapResponse:
    """Hourly pattern data for heatmap visualization, aggregated over trailing N days."""
    _validate_airport(airport)
    _validate_area(area)

    store = _store()
    _ensure_ready(store)
    as_of = _current_ts(store)
    start_date = (as_of - timedelta(days=days)).date()
    end_date = as_of.date()

    cells: list[HeatmapCell] = []

    with store.connect() as con:
        if area in config.SECURITY_AREAS:
            rows = con.execute(
                """
                SELECT ISODOW(obs_date) - 1 AS dow,
                       obs_hour,
                       AVG(wait_min_est) AS avg_wait,
                       AVG(pax) AS avg_pax
                FROM tsa_throughput
                WHERE grain = 'checkpoint_hour'
                  AND airport_code = ?
                  AND area_type = ?
                  AND obs_date BETWEEN ? AND ?
                GROUP BY ISODOW(obs_date) - 1, obs_hour
                ORDER BY dow, obs_hour
                """,
                [airport, area, start_date, end_date],
            ).fetchall()
        else:
            rows = con.execute(
                """
                SELECT ISODOW(CAST(ts AS DATE)) - 1 AS dow,
                       EXTRACT(HOUR FROM ts)::INTEGER AS hr,
                       AVG(wait_min) AS avg_wait,
                       AVG(queue_length) AS avg_pax
                FROM airport_ops
                WHERE airport_code = ?
                  AND area_type = ?
                  AND CAST(ts AS DATE) BETWEEN ? AND ?
                GROUP BY ISODOW(CAST(ts AS DATE)) - 1, EXTRACT(HOUR FROM ts)::INTEGER
                ORDER BY dow, hr
                """,
                [airport, area, start_date, end_date],
            ).fetchall()

    for row in rows:
        cells.append(
            HeatmapCell(
                day_of_week=int(row[0]),
                hour=int(row[1]),
                avg_wait_min=round(float(row[2]), 1) if row[2] is not None else 0.0,
                avg_pax=round(float(row[3]), 1) if row[3] is not None else 0.0,
            )
        )

    return HeatmapResponse(
        airport_code=airport,
        area_type=area,
        cells=cells,
    )


@app.get("/queues/forecast", response_model=ForecastResponse)
def queues_forecast(
    airport: str,
    horizon: int = Query(default=60, ge=1, le=180),
    area: str = "SECURITY_TSA",
    model: str = "prophet",
) -> ForecastResponse:
    _validate_airport(airport)
    _validate_area(area, security_only=True)
    _validate_model(model)

    store = _store()
    _ensure_ready(store)

    with store.connect() as con:
        origin, points = _forecast_points(
            con,
            airport=airport,
            area=area,
            model=model,
            target_origin=_current_origin(store),
            horizon=horizon,
        )

    return ForecastResponse(
        airport_code=airport,
        area_type=area,
        model_name=model,
        origin_ts=origin,
        horizon_min=horizon,
        points=points,
    )


@app.get("/anomalies/recent", response_model=RecentAnomaliesResponse)
def anomalies_recent(
    airport: str | None = None,
    hours: int = Query(default=24, ge=1, le=720),
) -> RecentAnomaliesResponse:
    if airport is not None:
        _validate_airport(airport)

    store = _store()
    _ensure_ready(store)
    as_of = _current_ts(store)
    window_start = as_of - timedelta(hours=hours)

    sql = """
        SELECT event_id, airport_code, area_type, detected_at, anomaly_type,
               detector, metric, observed_value, expected_value, score, severity,
               description
        FROM anomaly_events
        WHERE detected_at BETWEEN ? AND ?
    """
    params: list[object] = [window_start, as_of]
    if airport and airport != "ALL":
        sql += " AND airport_code = ?"
        params.append(airport)
    sql += " ORDER BY detected_at DESC, event_id DESC"

    with store.connect() as con:
        rows = con.execute(sql, params).fetchall()

    events = [
        AnomalyEvent(
            event_id=int(row[0]),
            airport_code=row[1],
            area_type=row[2],
            detected_at=row[3],
            anomaly_type=row[4],
            detector=row[5],
            metric=row[6],
            observed_value=round(float(row[7]), 3),
            expected_value=None if row[8] is None else round(float(row[8]), 3),
            score=round(float(row[9]), 3),
            severity=row[10],
            description=row[11],
        )
        for row in rows
    ]
    return RecentAnomaliesResponse(as_of=as_of, window_hours=hours, events=events)


@app.get("/staffing/recommend", response_model=StaffingResponse)
def staffing_recommend(
    airport: str,
    date: date,
    area: str = "SECURITY_TSA",
    sla_target: float = Query(default=config.SLA_TARGET_MIN, gt=0.0),
) -> StaffingResponse:
    _validate_airport(airport)
    _validate_area(area, security_only=True)

    store = _store()
    _ensure_ready(store)

    with store.connect() as con:
        rows = con.execute(
            """
            SELECT rec_hour, forecast_pax, recommended_lanes, recommended_staff,
                   expected_wait_min, sla_met
            FROM staffing_recommendations
            WHERE airport_code = ? AND rec_date = ? AND area_type = ?
            ORDER BY rec_hour
            """,
            [airport, date, area],
        ).fetchall()

        if not rows:
            hourly = con.execute(
                """
                SELECT obs_hour, pax
                FROM tsa_throughput
                WHERE grain = 'checkpoint_hour'
                  AND airport_code = ?
                  AND area_type = ?
                  AND obs_date = ?
                ORDER BY obs_hour
                """,
                [airport, area, date],
            ).fetchall()
            if not hourly:
                raise HTTPException(status_code=404, detail="No staffing rows available")

            mu = config.SERVICE_RATE_PER_LANE[area]
            cap = config.LANE_CAPS[area]
            rows = []
            for obs_hour, pax in hourly:
                lam = pax / 60.0
                lanes = min_lanes_for_sla(lam, mu, sla_target, cap)
                lanes = max(lanes, 2 if pax > 0 else 0)
                wait = mm_c_wait(lam, mu, lanes) if lanes > 0 else 0.0
                rows.append(
                    (
                        obs_hour,
                        pax,
                        lanes,
                        lanes * config.OFFICERS_PER_LANE,
                        wait,
                        wait <= sla_target,
                    )
                )

    hours = [
        StaffingHour(
            rec_hour=int(row[0]),
            forecast_pax=int(row[1]),
            recommended_lanes=int(row[2]),
            recommended_staff=int(row[3]),
            expected_wait_min=round(float(row[4]), 3),
            sla_met=bool(row[5]),
        )
        for row in rows
    ]
    totals = StaffingTotals(
        peak_lanes=max((item.recommended_lanes for item in hours), default=0),
        total_staff_hours=sum(item.recommended_staff for item in hours),
    )
    return StaffingResponse(
        airport_code=airport,
        rec_date=date,
        area_type=area,
        sla_target_min=round(float(sla_target), 3),
        hours=hours,
        totals=totals,
    )


@app.post("/simulate/what-if", response_model=WhatIfResponse)
def simulate_what_if(payload: WhatIfRequest) -> WhatIfResponse:
    airport = _validate_airport(payload.airport_code)
    area = _validate_area(payload.area_type, security_only=True)

    store = _store()
    _ensure_ready(store)

    with store.connect() as con:
        current = _current_security_rows(con, _current_ts(store), airport)
    if current.empty:
        raise HTTPException(status_code=404, detail="No current queue state available")

    current = current.set_index("area_type")
    if area not in current.index:
        raise HTTPException(status_code=404, detail="No current queue state for requested area")

    security_total = int(current["pax"].sum())
    baseline_row = current.loc[area]
    baseline_lanes = int(baseline_row["lanes_open"])
    baseline_ratio = 0.0
    if security_total > 0 and "SECURITY_PRECHECK" in current.index:
        baseline_ratio = float(current.loc["SECURITY_PRECHECK", "pax"]) / security_total

    if payload.use_current_arrivals:
        if security_total <= 0:
            arrival_rate = 0.0
        elif area == "SECURITY_PRECHECK":
            arrival_rate = (security_total * payload.precheck_ratio) / 60.0
        else:
            arrival_rate = (security_total * (1.0 - payload.precheck_ratio)) / 60.0
    else:
        if payload.arrival_rate_per_min is None:
            raise HTTPException(status_code=400, detail="arrival_rate_per_min is required when use_current_arrivals is false")
        arrival_rate = payload.arrival_rate_per_min

    scenario_result = simulate_checkpoint(
        arrival_rate_per_min=arrival_rate * payload.surge_multiplier,
        service_rate_per_lane=payload.service_rate_per_lane,
        num_lanes=payload.num_lanes,
        duration_min=payload.duration_min,
        sla_target_min=config.SLA_TARGET_MIN,
        seed=config.RANDOM_SEED + payload.num_lanes,
    )
    baseline_result = simulate_checkpoint(
        arrival_rate_per_min=(float(baseline_row["pax"]) / 60.0) * payload.surge_multiplier,
        service_rate_per_lane=config.SERVICE_RATE_PER_LANE[area],
        num_lanes=baseline_lanes,
        duration_min=payload.duration_min,
        sla_target_min=config.SLA_TARGET_MIN,
        seed=config.RANDOM_SEED + baseline_lanes,
    )

    scenario_metrics = _scenario_metrics(
        scenario_result,
        num_lanes=payload.num_lanes,
        precheck_ratio=payload.precheck_ratio,
    )
    baseline_metrics = _scenario_metrics(
        baseline_result,
        num_lanes=baseline_lanes,
        precheck_ratio=baseline_ratio,
    )

    return WhatIfResponse(
        scenario=scenario_metrics,
        baseline=baseline_metrics,
        delta=ScenarioDelta(
            mean_wait_min=round(
                scenario_metrics.mean_wait_min - baseline_metrics.mean_wait_min,
                3,
            ),
            sla_breach_min=scenario_metrics.sla_breach_min - baseline_metrics.sla_breach_min,
        ),
    )


@app.get("/dashboard/kpis", response_model=KpisResponse)
def dashboard_kpis(
    airport: str = "ALL",
    date_from: date | None = None,
    date_to: date | None = None,
) -> KpisResponse:
    airport = _validate_airport(airport)
    if date_from is None or date_to is None:
        raise HTTPException(status_code=422, detail="date_from and date_to are required")
    if date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from must be on or before date_to")

    store = _store()
    _ensure_ready(store)

    airport_filter = "" if airport == "ALL" else "AND airport_code = ?"
    params: list[object] = [date_from, date_to]
    if airport != "ALL":
        params.append(airport)

    with store.connect() as con:
        waits = con.execute(
            f"""
            SELECT airport_code, obs_date, obs_hour, pax, wait_min_est
            FROM tsa_throughput
            WHERE grain = 'checkpoint_hour'
              AND obs_date BETWEEN ? AND ?
              {airport_filter}
            """,
            params,
        ).fetchdf()
        daily = con.execute(
            f"""
            SELECT airport_code, obs_date, pax
            FROM tsa_throughput
            WHERE grain = 'daily'
              AND obs_date BETWEEN ? AND ?
              {airport_filter}
            """,
            params,
        ).fetchdf()
        anomaly_count = con.execute(
            f"""
            SELECT COUNT(*)
            FROM anomaly_events
            WHERE CAST(detected_at AS DATE) BETWEEN ? AND ?
              {"AND airport_code = ?" if airport != "ALL" else ""}
            """,
            params,
        ).fetchone()[0]

    if waits.empty or daily.empty:
        raise HTTPException(status_code=404, detail="No KPI rows available for the requested range")

    trend_waits = (
        waits.groupby("obs_date")
        .agg(
            avg_wait_min=("wait_min_est", "mean"),
            sla_breach_rate=("wait_min_est", lambda values: float((values >= config.BREACH_WAIT_MIN).mean())),
        )
        .reset_index()
    )
    trend_pax = daily.groupby("obs_date").agg(total_pax=("pax", "sum")).reset_index()
    trend = trend_waits.merge(trend_pax, on="obs_date", how="inner")

    busiest_airport = (
        daily.groupby("airport_code")["pax"].sum().sort_values(ascending=False).index[0]
        if airport == "ALL"
        else airport
    )
    busiest_hour = int(waits.groupby("obs_hour")["pax"].sum().idxmax())

    trend_payload = [
        KpiTrendPoint(
            obs_date=row["obs_date"],
            avg_wait_min=round(float(row["avg_wait_min"]), 3),
            total_pax=int(row["total_pax"]),
            sla_breach_rate=round(float(row["sla_breach_rate"]), 3),
        )
        for _, row in trend.iterrows()
    ]

    return KpisResponse(
        airport_code=airport,
        date_from=date_from,
        date_to=date_to,
        kpis=KpiSummary(
            avg_wait_min=round(float(waits["wait_min_est"].mean()), 3),
            p95_wait_min=round(float(waits["wait_min_est"].quantile(0.95)), 3),
            total_pax=int(daily["pax"].sum()),
            sla_breach_rate=round(float((waits["wait_min_est"] >= config.BREACH_WAIT_MIN).mean()), 3),
            anomaly_count=int(anomaly_count),
            busiest_airport=busiest_airport,
            busiest_hour=busiest_hour,
        ),
        trend=trend_payload,
    )


@app.get("/models", response_model=ModelsResponse)
def models() -> ModelsResponse:
    return ModelsResponse(
        models=[
            ModelDescriptor(
                name="prophet",
                label="Prophet (seasonality + regressors)",
                default=True,
                horizon_max_min=180,
            ),
            ModelDescriptor(
                name="nbeats",
                label="N-BEATS (deep, short-horizon)",
                default=False,
                horizon_max_min=120,
            ),
            ModelDescriptor(
                name="lstm",
                label="LSTM (Darts RNN)",
                default=False,
                horizon_max_min=120,
            ),
        ]
    )


@app.get("/config/clock", response_model=ClockResponse)
def get_clock() -> ClockResponse:
    store = _store()
    _ensure_ready(store)
    return ClockResponse(
        demo_now=_current_ts(store),
        min=store.min_demo_now,
        max=store.max_demo_now,
    )


@app.post("/config/clock", response_model=ClockResponse)
def update_clock(payload: ClockUpdateRequest) -> ClockResponse:
    store = _store()
    _ensure_ready(store)
    if payload.demo_now < store.min_demo_now or payload.demo_now > store.max_demo_now:
        raise HTTPException(status_code=400, detail="demo_now is outside the available data window")
    store.demo_now = payload.demo_now
    return ClockResponse(
        demo_now=store.demo_now,
        min=store.min_demo_now,
        max=store.max_demo_now,
    )
