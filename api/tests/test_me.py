import uuid
from collections.abc import Callable

from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.user import User, UserAuthMethod


async def _make_user(
    db: AsyncSession,
    *,
    supertokens_user_id: str,
    email: str,
    display_name: str | None,
    provider: str = "emailpassword",
) -> User:
    user = User(email=email, display_name=display_name)
    db.add(user)
    await db.flush()
    db.add(UserAuthMethod(user_id=user.id, provider=provider, supertokens_user_id=supertokens_user_id))
    await db.flush()
    return user


async def test_get_me_no_session(client: tuple[AsyncClient, FastAPI]) -> None:
    ac, _ = client
    response = await ac.get("/api/v1/me")
    assert response.status_code in (401, 500)


async def test_get_me_returns_user(
    authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await _make_user(
        db, supertokens_user_id="st-abc-123", email="gandalf@middleearth.com", display_name="Gandalf the Grey"
    )

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
    await _make_user(
        db, supertokens_user_id="st-social-456", email="aragorn@middleearth.com", display_name=None, provider="google"
    )

    ac = authenticated_client("st-social-456")
    response = await ac.get("/api/v1/me")
    assert response.status_code == 200
    assert response.json()["display_name"] is None


async def test_patch_me_sets_display_name(
    authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await _make_user(db, supertokens_user_id="st-patch-789", email="frodo@shire.com", display_name=None)

    ac = authenticated_client("st-patch-789")
    response = await ac.patch("/api/v1/me", json={"display_name": "Frodo Baggins"})
    assert response.status_code == 200
    data = response.json()
    assert uuid.UUID(data["id"]) == user.id
    assert data["display_name"] == "Frodo Baggins"

    refreshed = await db.scalar(select(User).where(User.id == user.id))
    assert refreshed.display_name == "Frodo Baggins"


async def test_patch_me_empty_string_rejected(
    authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    await _make_user(db, supertokens_user_id="st-empty-000", email="bilbo@shire.com", display_name="Bilbo")

    ac = authenticated_client("st-empty-000")
    response = await ac.patch("/api/v1/me", json={"display_name": "   "})
    assert response.status_code == 422


async def test_patch_me_too_long_rejected(
    authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    await _make_user(db, supertokens_user_id="st-long-111", email="sam@shire.com", display_name="Sam")

    ac = authenticated_client("st-long-111")
    response = await ac.patch("/api/v1/me", json={"display_name": "x" * 51})
    assert response.status_code == 422
