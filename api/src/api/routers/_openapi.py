from typing import Any

_Responses = dict[int | str, dict[str, Any]]

UNAUTHENTICATED: _Responses = {401: {"description": "Not authenticated"}}
FORBIDDEN: _Responses = {403: {"description": "Forbidden"}}
NOT_FOUND: _Responses = {404: {"description": "Not found"}}
CONFLICT: _Responses = {409: {"description": "Conflict"}}
