from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from supertokens_python.recipe.session import SessionContainer
from supertokens_python.recipe.session.framework.fastapi import verify_session

from api.models.user import User, UserAuthMethod


async def get_session(
    session: Annotated[SessionContainer, Depends(verify_session())],
) -> SessionContainer:
    return session


async def get_user_by_session(session: SessionContainer, db: AsyncSession) -> User | None:
    return await db.scalar(
        select(User)
        .join(UserAuthMethod, UserAuthMethod.user_id == User.id)
        .where(UserAuthMethod.supertokens_user_id == session.get_user_id())
    )
