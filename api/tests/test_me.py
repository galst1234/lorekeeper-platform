import uuid
from collections.abc import Callable

from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.user import User


async def test_get_me_no_session(client: tuple[AsyncClient, FastAPI]) -> None:
    ac, _ = client
    response = await ac.get("/api/v1/me")
    assert response.status_code in (401, 500)


async def test_get_me_returns_user(
    authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = User(
        supertokens_user_id="st-abc-123",
        email="gandalf@middleearth.com",
        display_name="Gandalf the Grey",
    )
    db.add(user)
    await db.flush()

    ac = authenticated_client("st-abc-123")
    response = await ac.get("/api/v1/me")
    assert response.status_code == 200
    data = response.json()
    assert uuid.UUID(data["id"]) == user.id
    assert data["email"] == "gandalf@middleearth.com"
    assert data["display_name"] == "Gandalf the Grey"


async def test_get_me_social_user_null_display_name(
    authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = User(
        supertokens_user_id="st-social-456",
        email="aragorn@middleearth.com",
        display_name=None,
    )
    db.add(user)
    await db.flush()

    ac = authenticated_client("st-social-456")
    response = await ac.get("/api/v1/me")
    assert response.status_code == 200
    assert response.json()["display_name"] is None


async def test_patch_me_sets_display_name(
    authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = User(
        supertokens_user_id="st-patch-789",
        email="frodo@shire.com",
        display_name=None,
    )
    db.add(user)
    await db.flush()

    ac = authenticated_client("st-patch-789")
    response = await ac.patch("/api/v1/me", json={"display_name": "Frodo Baggins"})
    assert response.status_code == 200
    data = response.json()
    assert uuid.UUID(data["id"]) == user.id
    assert data["display_name"] == "Frodo Baggins"

    result = await db.execute(select(User).where(User.supertokens_user_id == "st-patch-789"))
    assert result.scalar_one().display_name == "Frodo Baggins"


async def test_patch_me_empty_string_rejected(
    authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = User(
        supertokens_user_id="st-empty-000",
        email="bilbo@shire.com",
        display_name="Bilbo",
    )
    db.add(user)
    await db.flush()

    ac = authenticated_client("st-empty-000")
    response = await ac.patch("/api/v1/me", json={"display_name": "   "})
    assert response.status_code == 422


async def test_patch_me_too_long_rejected(
    authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = User(
        supertokens_user_id="st-long-111",
        email="sam@shire.com",
        display_name="Sam",
    )
    db.add(user)
    await db.flush()

    ac = authenticated_client("st-long-111")
    response = await ac.patch("/api/v1/me", json={"display_name": "x" * 51})
    assert response.status_code == 422
