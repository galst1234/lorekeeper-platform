import json
from pathlib import Path

from api.main import app


def main() -> None:
    schema = app.openapi()
    output_path = Path(__file__).resolve().parent.parent / "openapi.json"
    output_path.write_text(json.dumps(schema, indent=2) + "\n", newline="\n")


if __name__ == "__main__":
    main()
