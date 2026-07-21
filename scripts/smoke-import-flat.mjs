import { readFileSync } from "node:fs";
import { validateBytes } from "./src/js/importValidate.js";
const buf = readFileSync("./public/fixtures/example_valid_routine.json");
const r = validateBytes(buf, { filename: "example.json" });
console.log({ ok: r.ok, errors: r.errors, schema: r.preview?.schema_version, sessions: r.preview?.session_count });
if (!r.ok) process.exit(1);
