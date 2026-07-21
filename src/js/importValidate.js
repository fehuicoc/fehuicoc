/**
 * Client-side import validation (replaces FastAPI /api/import/preview).
 * Schemas 1.0 / 1.1 / 1.2 via JSON Schema draft 2020-12.
 */
import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import schema from "../contracts/exercise_routine_import.schema.json";

export const MAX_FILE_BYTES = 1_048_576;
export const FORMAT_ID = "exercise-routine-coach";

const ajv = new Ajv2020({ allErrors: true, strict: false });
addFormats(ajv);
const validateSchema = ajv.compile(schema);

function compatibleVersions() {
  const compat = schema.x_compatibility || {};
  const versions = compat.compatible_schema_versions || ["1.0", "1.1", "1.2"];
  return new Set(versions.map(String));
}

function extensionOk(filename) {
  if (!filename) return false;
  return String(filename).toLowerCase().endsWith(".json");
}

function optionalFieldWarnings(document) {
  const warnings = [];
  const routine = document.routine || {};
  const optionalTop = [
    "goal",
    "description",
    "level",
    "estimated_duration_minutes",
    "frequency",
    "equipment_required",
    "general_notes",
    "non_medical_warnings",
  ];
  const missing = optionalTop.filter((k) => !(k in routine));
  if (missing.length) {
    warnings.push(
      "Optional routine fields absent (non-blocking): " + missing.join(", ")
    );
  }
  for (const session of routine.sessions || []) {
    for (const ex of session.exercises || []) {
      if (!("visual_ref" in ex)) {
        warnings.push(
          `Exercise “${ex.name || ex.id || "?"}”: visual_ref absent — placeholder will be used in session.`
        );
        break;
      }
    }
  }
  return warnings;
}

function previewExercise(ex) {
  const metric = ex.metric || {};
  return {
    id: ex.id,
    name: ex.name,
    order: ex.order,
    sets: ex.sets,
    metric_kind: metric.kind,
    reps: metric.reps,
    min_reps: metric.min_reps,
    max_reps: metric.max_reps,
    duration_seconds: metric.duration_seconds,
    rest_seconds: ex.rest_seconds,
    transition_seconds: ex.transition_seconds,
    laterality: ex.laterality,
    load: ex.load,
  };
}

function previewFromDocument(document) {
  const routine = document.routine || {};
  const sessions = [];
  for (const session of routine.sessions || []) {
    const exercises = (session.exercises || []).map(previewExercise);
    const blocks = [];
    for (const block of session.blocks || []) {
      const blockExercises = (block.exercises || []).map(previewExercise);
      blocks.push({
        id: block.id,
        name: block.name,
        order: block.order,
        type: block.type,
        rounds: block.rounds,
        exercise_count: blockExercises.length,
        exercises: blockExercises,
      });
    }
    const exerciseCount =
      exercises.length ||
      blocks.reduce((n, b) => n + (b.exercise_count || 0), 0);
    sessions.push({
      id: session.id,
      name: session.name,
      order: session.order,
      exercise_count: exerciseCount,
      block_count: blocks.length,
      exercises,
      blocks,
    });
  }
  const live = routine.live_tracking || {};
  return {
    routine_id: routine.id,
    name: routine.name,
    schema_version: document.schema_version,
    session_count: sessions.length,
    sessions,
    live_tracking: Object.keys(live).length
      ? {
          countdown_before_start_seconds: live.countdown_before_start_seconds,
          allow_extend_rest: live.allow_extend_rest,
          rest_extension_increment_seconds:
            live.rest_extension_increment_seconds,
          display_preferences: live.display_preferences,
        }
      : null,
    persisted: false,
  };
}

/**
 * @param {ArrayBuffer|Uint8Array|string} content
 * @param {{ filename?: string, contentType?: string, checkExtension?: boolean }} [opts]
 */
export function validateBytes(content, opts = {}) {
  const {
    filename = null,
    contentType = null,
    checkExtension = true,
  } = opts;
  const errors = [];
  const warnings = [];

  if (checkExtension && !extensionOk(filename)) {
    return {
      ok: false,
      errors: [
        "Disallowed file extension — only .json import files are accepted.",
      ],
      warnings: [],
      document: null,
      preview: null,
    };
  }

  let bytes;
  if (typeof content === "string") {
    bytes = new TextEncoder().encode(content);
  } else if (content instanceof ArrayBuffer) {
    bytes = new Uint8Array(content);
  } else {
    bytes = content;
  }

  if (bytes.byteLength > MAX_FILE_BYTES) {
    return {
      ok: false,
      errors: [
        `File exceeds size limit of ${MAX_FILE_BYTES} bytes (${bytes.byteLength} bytes received).`,
      ],
      warnings: [],
      document: null,
      preview: null,
    };
  }

  if (contentType && !String(contentType).toLowerCase().includes("json")) {
    warnings.push(
      `Content-Type “${contentType}” is not application/json; continuing because extension/body gates passed.`
    );
  }

  let text;
  try {
    text = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  } catch {
    return {
      ok: false,
      errors: ["File is not valid UTF-8 text JSON."],
      warnings: [],
      document: null,
      preview: null,
    };
  }

  let document;
  try {
    document = JSON.parse(text);
  } catch (exc) {
    return {
      ok: false,
      errors: [`Malformed JSON — ${exc.message || "parse error"}.`],
      warnings: [],
      document: null,
      preview: null,
    };
  }

  if (!document || typeof document !== "object" || Array.isArray(document)) {
    return {
      ok: false,
      errors: ["Import root must be a JSON object."],
      warnings: [],
      document: null,
      preview: null,
    };
  }

  const version = String(document.schema_version || "");
  const compatible = compatibleVersions();
  if (version && !compatible.has(version)) {
    if (!version.startsWith("1.")) {
      return {
        ok: false,
        errors: [
          `Incompatible schema_version “${version}” — only majors 1.x are accepted (${[...compatible].sort().join(", ")}).`,
        ],
        warnings: [],
        document: null,
        preview: null,
      };
    }
    warnings.push(
      `schema_version “${version}” is not in the shipped compatibility list (${[...compatible].sort().join(", ")}); validating against current schema.`
    );
  }

  const valid = validateSchema(document);
  if (!valid) {
    const schemaErrors = (validateSchema.errors || []).slice(0, 12).map((err) => {
      const path = err.instancePath || "(root)";
      return `${path}: ${err.message}`;
    });
    return {
      ok: false,
      errors: schemaErrors.length ? schemaErrors : ["Schema validation failed."],
      warnings,
      document: null,
      preview: null,
    };
  }

  if (document.format_id !== FORMAT_ID) {
    return {
      ok: false,
      errors: [`format_id must be "${FORMAT_ID}".`],
      warnings,
      document: null,
      preview: null,
    };
  }

  warnings.push(...optionalFieldWarnings(document));
  return {
    ok: true,
    errors: [],
    warnings,
    document,
    preview: previewFromDocument(document),
  };
}

export async function validateFile(file) {
  const buf = await file.arrayBuffer();
  return validateBytes(buf, {
    filename: file.name,
    contentType: file.type,
  });
}
