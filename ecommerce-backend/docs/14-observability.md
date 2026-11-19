# 14 — Observability

## Logging

`src/app/core/logging.py` configures structlog once at import of `main.py`.

- **Development (`DEBUG=true`):** human-readable `ConsoleRenderer`.
- **Production:** JSON `JSONRenderer`.
- Output: stdout.
- Shared processors: contextvars merge, log level, ISO timestamp, stack info.
- Level from `LOG_LEVEL` (default `INFO`).

### Request context

`RequestContextMiddleware` binds:

```python
request_id, path, method
```

Every log in the request includes them. The response echoes `X-Request-ID`
(incoming header or a new UUID). `duration_ms` and `status_code` are logged on
completion under `request_completed`.

### Logging a request

```
{"event":"request_completed","status_code":200,"duration_ms":12,
 "request_id":"…","path":"/api/v1/products","method":"GET",
 "level":"info","timestamp":"2026-…"}
```

### Gaps

- `add_trace_context` exists but is not in the processor chain, so `trace_id` is
  not attached to logs automatically.
- No log sampling or redaction layer.
- Some jobs use f-strings in the event name (e.g.
  `logger.info(f"Product {id} indexed")`), which breaks structured event naming.

## Metrics

`prometheus-fastapi-instrumentator` exposes `/metrics` and instruments request
count/latency by route and status.

Custom metrics (`src/app/core/metrics.py`):

| Metric | Type | Labels |
|---|---|---|
| `orders_created_total` | Counter | — |
| `orders_failed_total` | Counter | `reason` = `empty_cart`, `insufficient_stock`, `internal_error` |
| `order_value_dollars` | Histogram | — |

Note: the histogram records whatever the order total is; the currency is
implicitly the store currency, not necessarily USD.

### Useful queries

```promql
rate(orders_created_total[5m])
rate(orders_failed_total[5m])
histogram_quantile(0.95, rate(order_value_dollars_bucket[5m]))
```

## Tracing

`src/app/core/tracing.py`:

- OTel `TracerProvider` with `service.name = APP_NAME`.
- OTLP gRPC exporter to `OTEL_EXPORTER_ENDPOINT` (default `localhost:4317`).
- Before configuring the exporter, it opens a TCP socket to check reachability
  (2 s timeout). If unreachable, it still installs a provider but logs
  `opentelemetry_skipped` and exports nothing.
- SQLAlchemy instrumentation wraps the sync engine.
- FastAPI instrumentation is provided by the OTel FastAPI package and
  `configure_tracing(app, engine)`.

Compose runs `otel/opentelemetry-collector` with
`otel-collector-config.yaml` exposing 4317 (gRPC) and 4318 (HTTP).

## Health

`GET /api/v1/health`:

```json
{ "status": "ok", "database": "up" }
```

- `SELECT 1` against PostgreSQL.
- Exceptions → `degraded` / `down`, still HTTP 200.
- Does **not** check Redis, Elasticsearch, SMTP, the worker, or OpenAI.
- No readiness vs liveness split, despite Docker/K8s usage.

## Request IDs

- Header: `X-Request-ID`.
- If absent, a UUID is generated.
- Echoed on the response.
- Bound to logs; not forwarded to downstream HTTP calls (there are almost none
  in the request path).

## Recommended improvements

1. Add `add_trace_context` to the structlog chain.
2. Split `/health/live` and `/health/ready`; include Redis/ES checks.
3. Add metrics for cache hit ratio, search latency/errors, job success/failure,
   chat latency, and DB pool saturation.
4. Add a `/health` timeout so a hanging DB doesn't hang the probe.
5. Propagate `traceparent` to OpenAI/SMTP where supported.
6. Add structured job IDs to logs.
7. Add alert rules for `orders_failed_total{reason="internal_error"}` and job
   queue depth.
