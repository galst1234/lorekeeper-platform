# Claude Code Instructions

## Adding a new SQLAlchemy model file

When adding a new model file under `src/api/models/`:

1. **Export it from the package** — add it to `src/api/models/__init__.py`:
   ```python
   from api.models.your_model import YourModel
   __all__ = [..., "YourModel"]
   ```

2. **Update the TID251 ban** — add an entry to `pyproject.toml` under
   `[tool.ruff.lint.flake8-tidy-imports.banned-api]`:
   ```toml
   "api.models.your_model".msg = "Import models from 'api.models' instead of submodules."
   ```

   **Why**: All model classes must be imported through `api.models` (the package `__init__.py`)
   so SQLAlchemy's mapper registry has every model registered before the first query runs.
   Importing directly from a submodule (e.g. `from api.models.campaign import Campaign`)
   bypasses `__init__.py` and can cause `configure_mappers()` to fail resolving string
   relationship targets like `relationship("Campaign", ...)` when tests run in isolation.

## Campaign-scoped entities and visibility

Any model representing a campaign-scoped entity (characters, items, chronicle entries, and similar future resources) must include a `restricted: Mapped[bool]` column (`nullable=False`, `server_default=text("false")`). This flag drives GM-only visibility filtering in the service layer — see `api/src/api/services/common/visibility.py`.
