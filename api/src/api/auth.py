from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from supertokens_python.recipe.session import SessionContainer
from supertokens_python.recipe.session.framework.fastapi import verify_session

from api.database import get_db
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


async def get_current_user(
    session: Annotated[SessionContainer, Depends(get_session)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    user = await get_user_by_session(session, db)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
