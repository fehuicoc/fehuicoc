/**
 * MOD-ER-LIBRARY â€” account-less multi-routine library (localStorage).
 * Normalizes legacy flat exercises[] â†’ sessions[] on load (AD-018).
 */
(function (global) {
  const STORAGE_KEY = "er_coach_routines_v1";

  function normalizeRoutine(routine) {
    if (!routine || typeof routine !== "object") return routine;
    const out = Object.assign({}, routine);
    const sessions = out.sessions;
    if (Array.isArray(sessions) && sessions.length) {
      out.sessions = sessions.map((s, idx) =>
        Object.assign({}, s, {
          id: s.id || "session-" + (idx + 1),
          name: s.name || "Session " + (idx + 1),
          order: s.order != null ? s.order : idx + 1,
          exercises: Array.isArray(s.exercises) ? s.exercises : [],
          blocks: Array.isArray(s.blocks) ? s.blocks : [],
        })
      );
      delete out.exercises;
      return out;
    }
    const exercises = Array.isArray(out.exercises) ? out.exercises : [];
    out.sessions = [
      {
        id: "session-1",
        name: "Session 1",
        order: 1,
        exercises: exercises,
        blocks: [],
      },
    ];
    delete out.exercises;
    return out;
  }

  function exerciseCount(routine) {
    const norm = normalizeRoutine(routine);
    return (norm.sessions || []).reduce((n, s) => {
      const blocks = s.blocks || [];
      if (blocks.length) {
        return (
          n +
          blocks.reduce(
            (bn, b) => bn + ((b.exercises && b.exercises.length) || 0),
            0
          )
        );
      }
      return n + ((s.exercises && s.exercises.length) || 0);
    }, 0);
  }

  function sortedSessions(routine) {
    const norm = normalizeRoutine(routine);
    return (norm.sessions || [])
      .slice()
      .sort((a, b) => (Number(a.order) || 0) - (Number(b.order) || 0));
  }

  function flattenForRunner(routine, sessionId) {
    const norm = normalizeRoutine(routine);
    const sessions = sortedSessions(norm);
    let chosen = sessions[0] || null;
    if (sessionId) {
      chosen = sessions.find((s) => s.id === sessionId) || chosen;
    }
    return {
      id: norm.id,
      name: norm.name || "Routine",
      source: norm.source,
      import_schema_version: norm.import_schema_version,
      live_tracking: norm.live_tracking || null,
      session_id: chosen ? chosen.id : null,
      session_name: chosen ? chosen.name : null,
      exercises: chosen ? chosen.exercises || [] : [],
      blocks: chosen ? chosen.blocks || [] : [],
      sessions: sessions,
    };
  }

  function withActiveSessionExercises(routine, exercises, sessionId) {
    const norm = normalizeRoutine(routine);
    const sessions = (norm.sessions || []).slice();
    if (!sessions.length) {
      sessions.push({
        id: "session-1",
        name: "Session 1",
        order: 1,
        exercises: exercises,
      });
    } else {
      let idx = 0;
      if (sessionId) {
        const found = sessions.findIndex((s) => s.id === sessionId);
        if (found >= 0) idx = found;
      }
      sessions[idx] = Object.assign({}, sessions[idx], { exercises: exercises });
    }
    norm.sessions = sessions;
    delete norm.exercises;
    return norm;
  }

  function loadAll() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) return [];
      return parsed.map(normalizeRoutine);
    } catch (_) {
      return [];
    }
  }

  function saveAll(routines) {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify(routines.map(normalizeRoutine))
    );
  }

  function upsert(routine) {
    const list = loadAll();
    const normalized = normalizeRoutine(routine);
    const idx = list.findIndex((r) => r.id === normalized.id);
    if (idx >= 0) list[idx] = normalized;
    else list.push(normalized);
    saveAll(list);
    return normalized;
  }

  function getById(id) {
    const found = loadAll().find((r) => r.id === id) || null;
    return found ? normalizeRoutine(found) : null;
  }

  function remove(id) {
    saveAll(loadAll().filter((r) => r.id !== id));
  }

  function newId() {
    return "rt_" + Date.now().toString(36) + "_" + Math.random().toString(36).slice(2, 8);
  }

  function startSession(routineId, sessionId) {
    sessionStorage.setItem("er_active_routine_id", routineId);
    if (sessionId) {
      sessionStorage.setItem("er_active_session_id", sessionId);
    } else {
      sessionStorage.removeItem("er_active_session_id");
    }
    window.location.href = "/session.html";
  }

  function getActiveRoutineId() {
    return sessionStorage.getItem("er_active_routine_id");
  }

  function getActiveSessionId() {
    return sessionStorage.getItem("er_active_session_id");
  }

  function clearActiveRoutine() {
    sessionStorage.removeItem("er_active_routine_id");
    sessionStorage.removeItem("er_active_session_id");
  }

  function renderLibraryPage() {
    const listEl = document.getElementById("library-list");
    const emptyEl = document.getElementById("library-empty");
    if (!listEl) return;
    const routines = loadAll();
    listEl.innerHTML = "";
    if (!routines.length) {
      if (emptyEl) emptyEl.hidden = false;
      return;
    }
    if (emptyEl) emptyEl.hidden = true;
    routines.forEach((r) => {
      const li = document.createElement("li");
      li.className = "routine-card";
      const count = exerciseCount(r);
      const sessions = sortedSessions(r);
      const multi = sessions.length > 1;
      li.innerHTML =
        "<div><h3></h3><p></p></div><div class='control-bar'></div>";
      li.querySelector("h3").textContent = r.name || "Untitled routine";
      const source =
        r.source === "import" ? " Â· imported" : " Â· personal browser save";
      li.querySelector("p").textContent =
        count +
        (count === 1 ? " exercise" : " exercises") +
        (multi ? " · " + sessions.length + " days/sessions" : "") +
        source;
      const actions = li.querySelector(".control-bar");
      if (multi) {
        const select = document.createElement("select");
        select.className = "session-picker";
        select.setAttribute("aria-label", "Choose day or session to start");
        sessions.forEach((s) => {
          const opt = document.createElement("option");
          opt.value = s.id;
          opt.textContent =
            (s.order != null ? "Day " + s.order + ": " : "") +
            (s.name || s.id);
          select.appendChild(opt);
        });
        actions.appendChild(select);
        const startBtn = document.createElement("button");
        startBtn.type = "button";
        startBtn.className = "btn btn-primary";
        startBtn.textContent = "Start session";
        startBtn.addEventListener("click", () =>
          startSession(r.id, select.value)
        );
        actions.appendChild(startBtn);
      } else {
        const startBtn = document.createElement("button");
        startBtn.type = "button";
        startBtn.className = "btn btn-primary";
        startBtn.textContent = "Start session";
        startBtn.addEventListener("click", () =>
          startSession(r.id, sessions[0] && sessions[0].id)
        );
        actions.appendChild(startBtn);
      }
      const editLink = document.createElement("a");
      editLink.className = "btn";
      editLink.href = "/author.html?id=" + encodeURIComponent(r.id);
      editLink.textContent = "Edit";
      const delBtn = document.createElement("button");
      delBtn.type = "button";
      delBtn.className = "btn";
      delBtn.textContent = "Delete";
      delBtn.addEventListener("click", () => {
        remove(r.id);
        renderLibraryPage();
      });
      actions.append(editLink, delBtn);
      listEl.appendChild(li);
    });
  }

  global.ERLibrary = {
    STORAGE_KEY,
    loadAll,
    saveAll,
    upsert,
    getById,
    remove,
    newId,
    startSession,
    getActiveRoutineId,
    getActiveSessionId,
    clearActiveRoutine,
    renderLibraryPage,
    normalizeRoutine,
    exerciseCount,
    sortedSessions,
    flattenForRunner,
    withActiveSessionExercises,
  };
})(window);
