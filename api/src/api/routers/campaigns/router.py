from api.routers.campaigns import characters, invites, items, members
from api.routers.campaigns.campaigns import detail_router, router

detail_router.include_router(invites.router)
detail_router.include_router(characters.router)
detail_router.include_router(items.router)
detail_router.include_router(members.router)
router.include_router(detail_router)
