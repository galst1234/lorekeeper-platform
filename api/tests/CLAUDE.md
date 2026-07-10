# Tests

Two test layers, deliberately different in what they mock — pick the one matching the directory you're writing in.

## `tests/routers/` — solitary unit tests

A router test verifies the *route's own logic only*: status codes, response shape, error mapping, and that it delegates to the right collaborator with the right arguments. It does not verify that the collaborator's underlying behavior is correct — that's the service test's job.

Mock every collaborator the route doesn't own:
- **Service-layer functions** (`api.services.*`) — patch them with `mocker.patch("api.services.characters.get_character_by_slug", return_value=...)`. Routers import services as a module alias (`from api.services import characters as character_service`), so patching the service module's own dotted path (`api.services.characters.func`) affects every caller — there's no need to patch per-router-module namespace.
- **Storage** (`ImageStorage`) — override the `get_image_storage` FastAPI dependency with `mocker.create_autospec(ImageStorage, instance=True)` instead of a real `LocalDiskStorage`.
- **Permission dependencies** (`require_campaign_member`, `require_campaign_owner`) — override them directly via `app.dependency_overrides` to return a fake `CampaignMember` (allowed) or raise `HTTPException(403)` (denied). Overriding a dependency short-circuits its entire sub-dependency tree (`get_campaign_or_404`, `get_current_user`, `get_db`), so a router test exercising a member/owner-gated route needs no real database or auth session at all.

Build fake ORM instances in memory with the `build_*` helpers in `tests/helpers.py` (`build_campaign`, `build_character`, `build_item`) — never persisted, never queried back. Use these instead of the `make_*` factories (which write real rows) in router tests.

Assert on both ends: the HTTP response, and that the mocked collaborator was called with the arguments the route should have passed it (`mock.assert_awaited_once_with(...)`) — or, for permission-denial tests, that it was *never* called (`mock.assert_not_called()`), proving the route short-circuits before touching downstream collaborators.

```python
async def test_upload_character_image_returns_200_with_image_url(
    image_client: tuple[AsyncClient, FastAPI, ImageStorage],
    mocker: MockerFixture,
) -> None:
    ac, inner_app, image_storage = image_client
    campaign = build_campaign()
    character = build_character(campaign_id=campaign.id, slug="aria")
    updated = build_character(campaign_id=campaign.id, slug="aria", image_key="new-key.jpg")
    _allow_member(inner_app, campaign)
    mocker.patch("api.services.characters.get_character_by_slug", return_value=character)
    mock_set = mocker.patch("api.services.characters.set_character_image", return_value=updated)
    image_storage.save.return_value = "new-key.jpg"
    image_storage.url_for.return_value = "/media/new-key.jpg"

    response = await ac.put(f"/api/v1/campaigns/{campaign.slug}/characters/aria/image", files=...)

    assert response.status_code == 200
    assert response.json()["image_url"] == "/media/new-key.jpg"
    mock_set.assert_awaited_once_with(ANY, character, "new-key.jpg", image_storage)
```

## `tests/services/` — sociable tests

A service test verifies real business logic against real infrastructure: the `db` fixture (a real Postgres connection, wrapped in a SAVEPOINT and rolled back after the test — see `conftest.py`) and, for anything storage-touching, a real `LocalDiskStorage` pointed at pytest's `tmp_path`. Assert against real state: query the row back, check the file actually exists or is actually gone. Don't mock the thing you're testing the business logic of.

## Mocking mechanics

- Use `pytest-mock`'s `mocker` fixture (`mocker.patch`, `mocker.create_autospec`, ...), not bare `unittest.mock.patch`/`monkeypatch`. `mocker.patch` gives a `Mock`/`AsyncMock` with call-assertion methods and auto-unpatches at teardown — no `with`/decorator bookkeeping.
- `mocker.patch(...)` auto-detects `async def` targets and returns an `AsyncMock` (Python 3.8+); no need for `new_callable=AsyncMock`.
- `mocker.create_autospec(SomeProtocol, instance=True)` correctly mixes `AsyncMock` for async methods and `MagicMock` for sync ones on the same object — the right choice for `ImageStorage`, which has both.
- FastAPI dependency overrides (`app.dependency_overrides[dep] = ...`) are the mechanism for anything wired through `Depends(...)` (storage, permission checks, DB session). Direct service-layer calls aren't DI'd — use `mocker.patch` for those instead.
