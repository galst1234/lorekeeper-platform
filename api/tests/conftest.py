from collections.abc import AsyncGenerator, Callable
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from api.auth import get_session
from api.config import settings
from api.database import Base, get_db

TEST_DATABASE_URL = settings.database_url.replace("/lorekeeper_platform", "/lorekeeper_platform_test")

_supertokens_initialized = False
_engine_container: dict[str, AsyncEngine] = {}


@pytest.fixture(scope="session", autouse=True)
async def create_test_tables() -> AsyncGenerator[None]:
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    _engine_container["engine"] = engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession]:
    engine = _engine_container["engine"]
    async with engine.connect() as conn:
        await conn.begin()
        async_session = AsyncSession(conn, expire_on_commit=False)
        await async_session.begin_nested()  # creates a SAVEPOINT

        yield async_session

        await async_session.rollback()  # rollback to savepoint
        await conn.rollback()  # rollback outer transaction


def make_mock_session(user_id: str) -> MagicMock:
    mock = MagicMock()
    mock.get_user_id.return_value = user_id
    return mock


@pytest.fixture
async def client(db: AsyncSession) -> AsyncGenerator[tuple[AsyncClient, FastAPI]]:
    from supertokens_python.framework.fastapi import get_middleware

    from api.routers import me as me_router
    from api.supertokens import init_supertokens

    global _supertokens_initialized
    if not _supertokens_initialized:
        init_supertokens()
        _supertokens_initialized = True

    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        yield db

    inner_app = FastAPI()
    inner_app.add_middleware(get_middleware())
    inner_app.include_router(me_router.router, prefix="/api/v1")
    inner_app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=inner_app), base_url="http://test") as ac:
        yield ac, inner_app


@pytest.fixture
def authenticated_client(client: tuple[AsyncClient, FastAPI]) -> Callable[[str], AsyncClient]:
    ac, inner_app = client

    def _with_user(user_id: str) -> AsyncClient:
        inner_app.dependency_overrides[get_session] = lambda: make_mock_session(user_id)
        return ac

    return _with_user
