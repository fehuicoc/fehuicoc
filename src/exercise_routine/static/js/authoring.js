/**
 * MOD-ER-AUTHORING — ordered dual-metric exercise editor (AD-015, AD-017).
 * Loads/saves active session exercises on the canonical sessions[] model.
 */
(function () {
  const rowsEl = document.getElementById("exercise-rows");
  const form = document.getElementById("author-form");
  if (!form || !rowsEl || !window.ERLibrary) return;

  function emptyExercise() {
    return {
      name: "",
      duration_seconds: "",
      reps: "",
      rest_seconds: "30",
      sets: "1",
      instructions: "",
      visual_url: "",
      transition_seconds: "",
    };
  }

  function hasMetric(ex) {
    const d = Number(ex.duration_seconds);
    const r = Number(ex.reps);
    return (Number.isFinite(d) && d > 0) || (Number.isFinite(r) && r > 0);
  }

  function addRow(data) {
    const ex = Object.assign(emptyExercise(), data || {});
    const card = document.createElement("fieldset");
    card.className = "exercise-card";
    card.innerHTML = `
      <h3>Exercise</h3>
      <label class="field"><span>Name</span>
        <input type="text" name="name" required maxlength="80"></label>
      <div class="field-grid">
        <label class="field"><span>Duration (seconds)</span>
          <input type="number" name="duration_seconds" min="0" step="1" inputmode="numeric"></label>
        <label class="field"><span>Reps target</span>
          <input type="number" name="reps" min="0" step="1" inputmode="numeric"></label>
        <label class="field"><span>Rest (seconds)</span>
          <input type="number" name="rest_seconds" min="0" step="1" inputmode="numeric"></label>
        <label class="field"><span>Sets</span>
          <input type="number" name="sets" min="1" step="1" inputmode="numeric"></label>
        <label class="field"><span>Transition (seconds, optional)</span>
          <input type="number" name="transition_seconds" min="0" step="1" inputmode="numeric"></label>
      </div>
      <label class="field"><span>Instructions</span>
        <textarea name="instructions" rows="2" maxlength="500"></textarea></label>
      <label class="field"><span>Visual URL (optional)</span>
        <input type="url" name="visual_url" placeholder="https://… or leave blank for placeholder"></label>
      <button type="button" class="btn btn-remove">Remove</button>
    `;
    card.querySelector('[name="name"]').value = ex.name;
    card.querySelector('[name="duration_seconds"]').value = ex.duration_seconds;
    card.querySelector('[name="reps"]').value = ex.reps;
    card.querySelector('[name="rest_seconds"]').value = ex.rest_seconds;
    card.querySelector('[name="sets"]').value = ex.sets;
    card.querySelector('[name="transition_seconds"]').value =
      ex.transition_seconds ?? "";
    card.querySelector('[name="instructions"]').value = ex.instructions;
    card.querySelector('[name="visual_url"]').value = ex.visual_url;
    card.querySelector(".btn-remove").addEventListener("click", () => {
      if (rowsEl.children.length <= 1) return;
      card.remove();
    });
    rowsEl.appendChild(card);
  }

  function readExercises() {
    return Array.from(rowsEl.querySelectorAll(".exercise-card")).map((card) => {
      const get = (n) => card.querySelector('[name="' + n + '"]').value.trim();
      const numOrNull = (v) => {
        if (v === "") return null;
        const n = Number(v);
        return Number.isFinite(n) ? n : null;
      };
      return {
        name: get("name"),
        duration_seconds: numOrNull(get("duration_seconds")),
        reps: numOrNull(get("reps")),
        rest_seconds: numOrNull(get("rest_seconds")) ?? 0,
        sets: Math.max(1, numOrNull(get("sets")) || 1),
        transition_seconds: numOrNull(get("transition_seconds")),
        instructions: get("instructions"),
        visual_url: get("visual_url") || null,
      };
    });
  }

  document.getElementById("btn-add-exercise").addEventListener("click", () => addRow());

  const params = new URLSearchParams(window.location.search);
  const editId = params.get("id");
  let editingId = null;
  let activeSessionId = null;
  let baseRoutine = null;

  if (editId) {
    const existing = window.ERLibrary.getById(editId);
    if (existing) {
      editingId = existing.id;
      baseRoutine = existing;
      document.getElementById("routine-name").value = existing.name || "";
      const sessions = window.ERLibrary.sortedSessions(existing);
      activeSessionId = sessions[0] ? sessions[0].id : null;
      const exercises =
        (sessions[0] && sessions[0].exercises) || existing.exercises || [];
      exercises.forEach((ex) =>
        addRow({
          name: ex.name || "",
          duration_seconds: ex.duration_seconds ?? "",
          reps: ex.reps ?? "",
          rest_seconds: ex.rest_seconds ?? "30",
          sets: ex.sets ?? "1",
          transition_seconds: ex.transition_seconds ?? "",
          instructions: ex.instructions || "",
          visual_url: ex.visual_url || "",
        })
      );
    }
  }
  if (!rowsEl.children.length) {
    addRow({
      name: "Goblet squat",
      duration_seconds: "45",
      reps: "12",
      rest_seconds: "30",
      sets: "2",
    });
    addRow({
      name: "Push-up",
      duration_seconds: "",
      reps: "10",
      rest_seconds: "30",
      sets: "2",
    });
  }

  form.addEventListener("submit", (ev) => {
    ev.preventDefault();
    const status = document.getElementById("form-status");
    const name = document.getElementById("routine-name").value.trim();
    const exercises = readExercises();
    if (!name) {
      status.className = "form-status error";
      status.textContent = "Give this routine a name.";
      return;
    }
    if (!exercises.length) {
      status.className = "form-status error";
      status.textContent = "Add at least one exercise.";
      return;
    }
    for (const ex of exercises) {
      if (!ex.name) {
        status.className = "form-status error";
        status.textContent = "Every exercise needs a name.";
        return;
      }
      if (!hasMetric(ex)) {
        status.className = "form-status error";
        status.textContent =
          ex.name +
          ": add a duration and/or reps target (both may be set; duration owns the timer).";
        return;
      }
    }
    let routine;
    if (baseRoutine) {
      routine = window.ERLibrary.withActiveSessionExercises(
        Object.assign({}, baseRoutine, { name }),
        exercises,
        activeSessionId
      );
      routine.id = editingId;
      routine.source = baseRoutine.source || "manual";
      routine.updated_at = new Date().toISOString();
    } else {
      routine = {
        id: editingId || window.ERLibrary.newId(),
        name,
        source: "manual",
        updated_at: new Date().toISOString(),
        sessions: [
          {
            id: "session-1",
            name: "Session 1",
            order: 1,
            exercises,
          },
        ],
      };
    }
    window.ERLibrary.upsert(routine);
    status.className = "form-status ok";
    status.textContent = "Saved “" + name + "”. Opening My routines…";
    setTimeout(() => {
      window.location.href = "/library";
    }, 600);
  });
})();
