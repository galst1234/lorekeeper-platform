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
