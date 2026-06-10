import logging

import sentry_sdk
from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs._internal.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from agent.config import settings


def setup_observability() -> tuple[trace.Tracer, metrics.Meter]:
    logging.basicConfig()

    if not settings.enable_tracing:
        return trace.get_tracer("lorekeeper-platform-agent"), metrics.get_meter("lorekeeper-platform-agent")

    sentry_sdk.init(
        dsn=settings.sentry_agent_dsn,
        send_default_pii=True,
        enable_logs=True,
        traces_sample_rate=1.0,
        server_name="lorekeeper-platform-agent",
    )

    resource = Resource({SERVICE_NAME: "lorekeeper-platform-agent"})
    auth_header = {"Authorization": f"Basic {settings.open_observe_api_key}"}

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint=f"{settings.open_observe_url}/api/default/v1/traces",
                headers=auth_header,
            ),
        ),
    )
    trace.set_tracer_provider(tracer_provider)

    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[
            PeriodicExportingMetricReader(
                OTLPMetricExporter(
                    endpoint=f"{settings.open_observe_url}/api/default/v1/metrics",
                    headers=auth_header,
                ),
            ),
        ],
    )
    metrics.set_meter_provider(meter_provider)

    logger_provider = LoggerProvider(resource=resource)
    set_logger_provider(logger_provider)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(
            OTLPLogExporter(
                endpoint=f"{settings.open_observe_url}/api/default/v1/logs",
                headers={**auth_header, "stream-name": "python"},
            ),
        ),
    )
    root_logger = logging.getLogger()
    root_logger.addHandler(LoggingHandler(level=logging.DEBUG, logger_provider=logger_provider))

    return trace.get_tracer("lorekeeper-platform-agent"), metrics.get_meter("lorekeeper-platform-agent")
