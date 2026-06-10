from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from supertokens_python import get_all_cors_headers
from supertokens_python.framework.fastapi import get_middleware

from api.config import settings
from api.observability import setup_observability
from api.routers import me as me_router
from api.supertokens import init_supertokens

setup_observability()
init_supertokens()

app = FastAPI(title="Lorekeeper Platform API")
FastAPIInstrumentor.instrument_app(app)
app.add_middleware(get_middleware())
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "PUT", "POST", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", *get_all_cors_headers()],
)
app.include_router(me_router.router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
