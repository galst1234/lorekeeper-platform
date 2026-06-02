from typing import Annotated

from fastapi import Depends
from supertokens_python.recipe.session import SessionContainer
from supertokens_python.recipe.session.framework.fastapi import verify_session


async def get_session(
    session: Annotated[SessionContainer, Depends(verify_session())],
) -> SessionContainer:
    return session
