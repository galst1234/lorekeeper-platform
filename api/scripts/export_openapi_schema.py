import json
from pathlib import Path

from api.main import app
from api.routers.common.campaign_entity import (
    CampaignEntityCreateModel,
    CampaignEntityPatchModel,
    CampaignEntityResponse,
)

_EXTRA_SCHEMAS = [CampaignEntityResponse, CampaignEntityCreateModel, CampaignEntityPatchModel]


def main() -> None:
    schema = app.openapi()
    for model in _EXTRA_SCHEMAS:
        schema["components"]["schemas"][model.__name__] = model.model_json_schema(
            ref_template="#/components/schemas/{model}"
        )
    output_path = Path(__file__).resolve().parent.parent / "openapi.json"
    output_path.write_text(json.dumps(schema, indent=2) + "\n", newline="\n")


if __name__ == "__main__":
    main()
