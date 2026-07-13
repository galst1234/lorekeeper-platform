from typing import Any

_Responses = dict[int | str, dict[str, Any]]

UNAUTHENTICATED: _Responses = {401: {"description": "Not authenticated"}}
FORBIDDEN: _Responses = {403: {"description": "Forbidden"}}
NOT_FOUND: _Responses = {404: {"description": "Not found"}}
CONFLICT: _Responses = {409: {"description": "Conflict"}}
INVALID_IMAGE: _Responses = {400: {"description": "Image is not a supported type or exceeds the size limit"}}
UNPROCESSABLE: _Responses = {422: {"description": "Validation failed"}}
