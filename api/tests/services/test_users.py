from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import User
from api.services.users import update_display_name
from tests.helpers import make_user


async def test_update_display_name_persists(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-user-update", email="svc-user-update@test.com")

    updated = await update_display_name(db, user, "New Name")

    assert updated.display_name == "New Name"
    refreshed = await db.scalar(select(User).where(User.id == user.id))
    assert refreshed is not None
    assert refreshed.display_name == "New Name"
