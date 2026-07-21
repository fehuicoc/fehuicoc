import { readFileSync } from "node:fs";
import { validateBytes } from "./src/js/importValidate.js";
import { adaptImportDocument } from "./src/js/importAdapter.js";

const buf = readFileSync("./public/fixtures/francisco_semana6_dia1_webapp_v2.json");
const r = validateBytes(buf, {
  filename: "francisco.json",
  contentType: "application/json",
});
console.log(
  JSON.stringify(
    {
      ok: r.ok,
      errors: r.errors,
      warning_count: (r.warnings || []).length,
      sessions: r.preview && r.preview.session_count,
      schema: r.preview && r.preview.schema_version,
    },
    null,
    2
  )
);
if (!r.ok) process.exit(1);
const c = adaptImportDocument(r.document);
const session0 = (c.sessions || [])[0] || {};
console.log(
  JSON.stringify(
    {
      canonical_id: c.id,
      sessions: (c.sessions || []).length,
      blocks: (session0.blocks || []).length,
      flat_exercises: (session0.exercises || []).length,
    },
    null,
    2
  )
);
