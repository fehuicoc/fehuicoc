/**
 * Map validated import DTO → canonical internal routine model (client-side).
 */

function asText(value) {
  if (value == null) return "";
  if (Array.isArray(value)) {
    return value.filter((item) => item != null).map(String).join("\n");
  }
  return String(value);
}

function asList(value) {
  if (value == null) return [];
  if (Array.isArray(value)) return [...value];
  return [value];
}

function mapMetric(metric) {
  const kind = metric.kind;
  let reps = null;
  let duration_seconds = null;
  let min_reps = metric.min_reps;
  let max_reps = metric.max_reps;
  if (kind === "reps" || kind === "reps_per_side") {
    reps = metric.reps != null ? Number(metric.reps) : null;
  } else if (kind === "duration" || kind === "duration_per_side") {
    duration_seconds =
      metric.duration_seconds != null ? Number(metric.duration_seconds) : null;
  } else if (kind === "rep_range") {
    if (min_reps != null) min_reps = Number(min_reps);
    if (max_reps != null) max_reps = Number(max_reps);
    if (max_reps != null) reps = Number(max_reps);
  }
  return {
    metric_kind: kind,
    reps,
    duration_seconds,
    min_reps,
    max_reps,
    stop_rule: metric.stop_rule,
  };
}

function mapExercise(ex) {
  const metric = mapMetric(ex.metric || {});
  const transition = ex.transition_seconds;
  const visual_ref = ex.visual_ref;
  const instructions =
    ex.instructions || asText(ex.execution_instructions);
  return {
    id: ex.id,
    name: ex.name,
    order: ex.order,
    sets: ex.sets != null ? Number(ex.sets) : 1,
    duration_seconds: metric.duration_seconds,
    reps: metric.reps,
    metric_kind: metric.metric_kind,
    min_reps: metric.min_reps,
    max_reps: metric.max_reps,
    stop_rule: metric.stop_rule,
    rest_seconds: Number(ex.rest_seconds || 0),
    transition_seconds: transition != null ? Number(transition) : null,
    instructions,
    execution_instructions: asList(ex.execution_instructions),
    visual_url: visual_ref || null,
    laterality: ex.laterality,
    side_sequence: [...(ex.side_sequence || [])],
    equipment: [...(ex.equipment || [])],
    load: ex.load != null ? structuredClone(ex.load) : null,
    setup: ex.setup != null ? structuredClone(ex.setup) : null,
    tempo: ex.tempo,
    technical_notes: Array.isArray(ex.technical_notes)
      ? asList(ex.technical_notes)
      : ex.technical_notes
        ? asText(ex.technical_notes)
        : "",
    common_errors: [...(ex.common_errors || [])],
    pain_adaptation: ex.pain_adaptation || "",
    alternatives: [...(ex.alternatives || [])],
  };
}

function mapBlock(block) {
  const exercises = (block.exercises || []).map(mapExercise);
  exercises.sort((a, b) => Number(a.order || 0) - Number(b.order || 0));
  return {
    id: block.id,
    name: block.name,
    order: Number(block.order || 0),
    type: block.type,
    rounds: block.rounds != null ? Number(block.rounds) : 1,
    rest_between_rounds_seconds:
      block.rest_between_rounds_seconds != null
        ? Number(block.rest_between_rounds_seconds)
        : null,
    transition_after_block_seconds:
      block.transition_after_block_seconds != null
        ? Number(block.transition_after_block_seconds)
        : null,
    estimated_duration_seconds: block.estimated_duration_seconds,
    exercises,
  };
}

function mapSession(session) {
  const blocks = (session.blocks || []).map(mapBlock);
  blocks.sort((a, b) => Number(a.order || 0) - Number(b.order || 0));
  const exercises = (session.exercises || []).map(mapExercise);
  exercises.sort((a, b) => Number(a.order || 0) - Number(b.order || 0));
  const out = {
    id: session.id,
    name: session.name,
    order: Number(session.order || 0),
    description: session.description || "",
    approx_duration_minutes: session.approx_duration_minutes,
    reserved_duration_minutes: session.reserved_duration_minutes,
    session_type: session.session_type,
    target_rpe: session.target_rpe,
    completion_rule: session.completion_rule,
    exercises,
    blocks,
  };
  if ("post_session_checkin" in session) {
    out.post_session_checkin = structuredClone(session.post_session_checkin);
  }
  return out;
}

function mapLiveTracking(live) {
  if (!live) return null;
  const prefs = live.display_preferences || {};
  return {
    countdown_before_start_seconds: live.countdown_before_start_seconds,
    auto_start_next_step: live.auto_start_next_step,
    allow_skip_step: live.allow_skip_step,
    allow_pause: live.allow_pause,
    allow_extend_rest: live.allow_extend_rest,
    rest_extension_increment_seconds: live.rest_extension_increment_seconds,
    audio_cues:
      live.audio_cues != null ? structuredClone(live.audio_cues) : null,
    display_preferences: {
      large_primary_numbers: prefs.large_primary_numbers,
      show_current_set: prefs.show_current_set,
      show_total_sets: prefs.show_total_sets,
      show_next_exercise: prefs.show_next_exercise,
      show_load: prefs.show_load,
      show_side: prefs.show_side,
      show_block_progress: prefs.show_block_progress,
      show_elapsed_time: prefs.show_elapsed_time,
      show_estimated_time_remaining: prefs.show_estimated_time_remaining,
    },
  };
}

function normalizeRoutine(routine) {
  if (!routine || typeof routine !== "object") return routine;
  const out = { ...routine };
  const sessions = out.sessions;
  if (Array.isArray(sessions) && sessions.length) {
    out.sessions = sessions.map((s, idx) => ({
      ...s,
      id: s.id || "session-" + (idx + 1),
      name: s.name || "Session " + (idx + 1),
      order: s.order != null ? s.order : idx + 1,
      exercises: Array.isArray(s.exercises) ? s.exercises : [],
      blocks: Array.isArray(s.blocks)
        ? s.blocks.map((b, bidx) => ({
            ...b,
            id: b.id || "block-" + (bidx + 1),
            name: b.name || "Block " + (bidx + 1),
            order: b.order != null ? b.order : bidx + 1,
            type: b.type || "sequence",
            rounds: b.rounds != null ? b.rounds : 1,
            exercises: Array.isArray(b.exercises) ? b.exercises : [],
          }))
        : [],
    }));
    delete out.exercises;
    if (out.live_tracking == null) delete out.live_tracking;
    return out;
  }
  const exercises = Array.isArray(out.exercises) ? out.exercises : [];
  out.sessions = [
    {
      id: "session-1",
      name: "Session 1",
      order: 1,
      exercises,
      blocks: [],
    },
  ];
  delete out.exercises;
  return out;
}

export function adaptImportDocument(document) {
  const routine = structuredClone(document.routine || {});
  const sessions = (routine.sessions || []).map(mapSession);
  sessions.sort((a, b) => Number(a.order || 0) - Number(b.order || 0));

  const metadata = {};
  for (const key of [
    "goal",
    "description",
    "level",
    "estimated_duration_minutes",
    "reserved_duration_minutes",
    "frequency",
    "equipment_required",
    "general_notes",
    "non_medical_warnings",
  ]) {
    if (key in routine) metadata[key] = routine[key];
  }

  const canonical = {
    id: routine.id,
    name: routine.name,
    source: "import",
    import_schema_version: document.schema_version,
    metadata: Object.keys(metadata).length ? metadata : null,
    live_tracking: mapLiveTracking(routine.live_tracking),
    sessions,
    updated_at: null,
  };
  return normalizeRoutine(canonical);
}
