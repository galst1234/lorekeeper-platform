from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from agent.observability import setup_observability

setup_observability()

app = FastAPI(title="Lorekeeper Agent")
FastAPIInstrumentor.instrument_app(app)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
