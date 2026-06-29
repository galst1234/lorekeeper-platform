from api.routers.campaigns import characters, invites, join
from api.routers.campaigns.campaigns import detail_router, router

detail_router.include_router(invites.router)
detail_router.include_router(join.router)
detail_router.include_router(characters.router)
router.include_router(detail_router)
