# Routers

Each API resource lives in its own file named after the resource. Top-level resources that have sub-resources become a package instead of a single file.

## Router packages

```
resource/
├── __init__.py        — re-exports `router` from router.py
├── resource.py        — schemas, helpers, and route handlers for the primary resource
├── router.py          — thin assembly
├── dependencies.py    — FastAPI dependencies shared across the package
└── sub_resource.py    — sub-resource file (see below)
```

## Sub-resource files

Each sub-resource file owns its prefix so route decorators stay clean:

```python
router = APIRouter(prefix="/items")

@router.get("")           # GET  /{resource}/{id}/items
@router.post("")          # POST /{resource}/{id}/items
@router.delete("/{id}")   # DELETE /{resource}/{id}/items/{id}
```

## Assembly (router.py)

Imports `router` from the primary resource file and mounts sub-routers onto them. No route handlers live here.

The primary resource file must not import from sub-resource files — keep the dependency graph acyclic.

## OpenAPI documentation

All routes and request/response models must be well documented for the public API schema.

**Tags** — set `tags=[...]` on the `APIRouter` when there is no tag-inheritance risk; otherwise set it on each route decorator individually. Tag names must be listed in `main.py`'s `openapi_tags` with a one-line description.

**Error responses** — every route must declare its possible error status codes via the `responses=` parameter. Use the shared constants from `routers/_openapi.py` for common codes; inline a dict for one-off cases:

```python
from api.routers._openapi import FORBIDDEN, NOT_FOUND, UNAUTHENTICATED

@router.get("", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
@router.post("", responses=UNAUTHENTICATED | {409: {"description": "Slug already taken"}})
```

Add a new constant to `_openapi.py` when the same status code + description is used across multiple routes.

**Summaries** — add `summary="..."` to route decorators whose HTTP method + path does not make the intent obvious (e.g. two `POST` routes on the same resource with different meanings).

**Examples** — every Pydantic request and response model must include a realistic example via `model_config`:

```python
from pydantic import BaseModel, ConfigDict

class ThingResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"id": "abc123", "name": "My Thing"}})
    id: str
    name: str
```

## Visibility filtering

List and get routes for campaign-scoped entities (characters, items, chronicle entries, locations, and similar future resources) must filter through `apply_visibility_filter` (`api/src/api/services/common/visibility.py`) in their service-layer implementation, so restricted entities never reach non-GM members.
