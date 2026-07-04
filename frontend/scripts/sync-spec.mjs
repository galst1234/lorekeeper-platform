import { copyFileSync, existsSync } from "node:fs";

const apiDir = "../api";
const source = "../api/openapi.json";
const destination = "openapi.json";

if (existsSync(source)) {
  copyFileSync(source, destination);
} else if (existsSync(apiDir)) {
  throw new Error(`Found ${apiDir} but no openapi.json inside it. Run the export script in api/ first.`);
} else if (!existsSync(destination)) {
  throw new Error(`Cannot find OpenAPI spec at ${source} or ${destination}`);
}
