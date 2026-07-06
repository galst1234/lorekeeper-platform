# Tests

`AGENTS.md` is a symlink to this file — edit only `CLAUDE.md`.

Two layers: **router tests** exercise HTTP behavior; **service tests** exercise database logic directly. Add both when introducing a new resource.

## Router tests (`tests/routers/`)

Test status codes, auth, validation, and response shape — not SQLAlchemy internals.

**Naming** — `test_{action}_{resource}_returns_{status}` or `test_{action}_{resource}_{scenario}`:

```python
async def test_list_items_returns_200(...) -> None: ...
async def test_get_item_returns_404_for_wrong_campaign(...) -> None: ...
```

**Sections** — group by HTTP verb with `# --- List ---`, `# --- Create ---`, etc.

**Fixtures** — use `campaigns_authenticated_client(supertokens_user_id)` for campaign routes, `authenticated_client` for `/me`. Pass the same `supertokens_user_id` string used in `make_user`.

**Auth coverage** — for each mutating and listing endpoint, include at least:
- happy path (member)
- `403` for authenticated non-member
- `404` when the resource is absent or belongs to another campaign

**Validation** — assert `422` for empty names, invalid slugs, and reserved slugs (`new`).

## Service tests (`tests/services/`)

Call service functions with the `db` fixture. No HTTP client, no status codes.

Cover persistence, ordering, filtering, slug conflicts, and cross-campaign isolation. Name tests `test_{function}_{scenario}` with a `svc-{resource}-` prefix in fixture IDs.

## Shared setup

**`conftest.py`** — session-scoped table create/drop against `lorekeeper_platform_test`; per-test `db` uses a savepoint and always rolls back. SuperTokens is mocked; no SuperTokens container is required.

**`helpers.py`** — factory functions (`make_user`, `make_campaign`, `make_item`, …) build rows via `db.add` + `flush`. Add a `make_*` helper for each new model.

**Test data IDs** — keep `supertokens_user_id`, email, and `slug_id` unique and grep-friendly per test:

| Layer  | Prefix example      | `slug_id` example |
|--------|---------------------|-------------------|
| Router | `rt-itm-list-200`   | `rtil0001`        |
| Service| `svc-itm-list-empty`| `itml0001`        |

## Running tests

```bash
uv run pytest                              # all tests
uv run pytest tests/routers/test_items.py  # one file
uv run pytest tests/routers/test_items.py::test_list_items_returns_200  # one test
```

Requires Postgres and a `lorekeeper_platform_test` database (see CI or local dev setup).
