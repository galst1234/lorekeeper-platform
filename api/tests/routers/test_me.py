import uuid
from unittest.mock import ANY

from fastapi import FastAPI
from httpx import AsyncClient
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from api.models import User
from tests.helpers import build_user


def _authenticate(inner_app: FastAPI, user: User) -> None:
    inner_app.dependency_overrides[get_current_user] = lambda: user


async def test_get_me_no_session(client: tuple[AsyncClient, FastAPI]) -> None:
    ac, _ = client
    response = await ac.get("/api/v1/me")
    assert response.status_code in (401, 500)


async def test_get_me_returns_user(client: tuple[AsyncClient, FastAPI]) -> None:
    ac, inner_app = client
    user = build_user(email="gandalf@middleearth.com", display_name="Gandalf the Grey")
    _authenticate(inner_app, user)

    response = await ac.get("/api/v1/me")

    assert response.status_code == 200
    data = response.json()
    assert uuid.UUID(data["id"]) == user.id
    assert data["email"] == "gandalf@middleearth.com"
    assert data["display_name"] == "Gandalf the Grey"


async def test_get_me_social_user_null_display_name(client: tuple[AsyncClient, FastAPI]) -> None:
    ac, inner_app = client
    user = build_user(email="aragorn@middleearth.com", display_name=None)
    _authenticate(inner_app, user)

    response = await ac.get("/api/v1/me")

    assert response.status_code == 200
    assert response.json()["display_name"] is None


async def test_patch_me_sets_display_name(
    client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = client
    user = build_user(email="frodo@shire.com", display_name=None)
    _authenticate(inner_app, user)

    async def _apply_update(_db: AsyncSession, target_user: User, display_name: str) -> User:
        target_user.display_name = display_name
        return target_user

    mock_update = mocker.patch("api.services.users.update_display_name", side_effect=_apply_update)

    response = await ac.patch("/api/v1/me", json={"display_name": "Frodo Baggins"})

    assert response.status_code == 200
    data = response.json()
    assert uuid.UUID(data["id"]) == user.id
    assert data["display_name"] == "Frodo Baggins"
    mock_update.assert_awaited_once_with(ANY, user, "Frodo Baggins")


async def test_patch_me_empty_string_rejected(
    client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = client
    _authenticate(inner_app, build_user(email="bilbo@shire.com", display_name="Bilbo"))
    mock_update = mocker.patch("api.services.users.update_display_name")

    response = await ac.patch("/api/v1/me", json={"display_name": "   "})

    assert response.status_code == 422
    mock_update.assert_not_called()


async def test_patch_me_too_long_rejected(
    client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = client
    _authenticate(inner_app, build_user(email="sam@shire.com", display_name="Sam"))
    mock_update = mocker.patch("api.services.users.update_display_name")

    response = await ac.patch("/api/v1/me", json={"display_name": "x" * 51})

    assert response.status_code == 422
    mock_update.assert_not_called()
