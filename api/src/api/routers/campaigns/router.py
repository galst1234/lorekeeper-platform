from api.routers.campaigns import characters, invites, join, members
from api.routers.campaigns.campaigns import detail_router, router

detail_router.include_router(invites.router)
detail_router.include_router(join.router)
detail_router.include_router(characters.router)
detail_router.include_router(members.router)
router.include_router(detail_router)
