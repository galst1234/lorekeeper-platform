from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from supertokens_python import get_all_cors_headers
from supertokens_python.framework.fastapi import get_middleware

from api.config import settings
from api.observability import setup_observability
from api.routers import campaigns as campaigns_router
from api.routers import me as me_router
from api.supertokens import init_supertokens

setup_observability()
init_supertokens()

app = FastAPI(
    title="Lorekeeper Platform API",
    openapi_tags=[
        {"name": "Me", "description": "Current user profile."},
        {"name": "Campaigns", "description": "Campaign management — create, read, update, and delete campaigns."},
        {"name": "Characters", "description": "Character management within a campaign."},
        {"name": "Items", "description": "Item management within a campaign."},
        {"name": "Chronicle", "description": "Chronicle entries — the campaign's session-by-session narrative record."},
        {"name": "Members", "description": "Campaign membership — list who is in a campaign."},
        {"name": "Invites", "description": "Invite links — generate, revoke, preview, and join via invite."},
    ],
)
FastAPIInstrumentor.instrument_app(app)
app.add_middleware(get_middleware())
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "PUT", "POST", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", *get_all_cors_headers()],
)
router = APIRouter(prefix="/api/v1")
router.include_router(me_router.router)
router.include_router(campaigns_router.router)
app.include_router(router)


@app.get("/health", tags=["Health"], include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}
