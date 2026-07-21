/**
 * Import page entry — client-only validate + adapt (no FastAPI).
 */
import { MAX_FILE_BYTES, validateFile } from "./importValidate.js";
import { adaptImportDocument } from "./importAdapter.js";

const PREVIEW_KEY = "er_import_preview_v1";

window.ER_MAX_FILE_BYTES = MAX_FILE_BYTES;

const fileInput = document.getElementById("import-file");
const dropzone = document.getElementById("import-dropzone");
const btnChoose = document.getElementById("btn-choose-file");
const statusEl = document.getElementById("import-status");
const validating = document.getElementById("import-validating");
const errorsBox = document.getElementById("import-errors");
const errorList = document.getElementById("import-error-list");
const warningsBox = document.getElementById("import-warnings");
const warningList = document.getElementById("import-warning-list");
const previewBox = document.getElementById("import-preview");
const previewSummary = document.getElementById("preview-summary");
const previewSessions = document.getElementById("preview-sessions");
const collisionPanel = document.getElementById("collision-panel");
const btnConfirm = document.getElementById("btn-confirm-import");
const btnCancel = document.getElementById("btn-cancel-import");
const btnRetry = document.getElementById("btn-retry-import");
const btnReplace = document.getElementById("btn-replace-id");
const btnCopy = document.getElementById("btn-copy-id");
const btnEditAfter = document.getElementById("btn-edit-after");

if (!fileInput || !window.ERLibrary) {
  console.error("Import page missing file input or ERLibrary");
} else {
  let pendingCanonical = null;
  let collisionChoice = null;

  function setStatus(text, kind) {
    if (!statusEl) return;
    statusEl.textContent = text || "";
    statusEl.className = "form-status" + (kind ? " " + kind : "");
  }

  function clearPreviewStore() {
    try {
      sessionStorage.removeItem(PREVIEW_KEY);
    } catch (_) {
      /* ignore */
    }
  }

  function savePreviewStore(payload) {
    try {
      sessionStorage.setItem(PREVIEW_KEY, JSON.stringify(payload));
    } catch (_) {
      /* ignore quota */
    }
  }

  function resetUi() {
    validating.hidden = true;
    errorsBox.hidden = true;
    warningsBox.hidden = true;
    previewBox.hidden = true;
    collisionPanel.hidden = true;
    errorList.innerHTML = "";
    warningList.innerHTML = "";
    previewSessions.innerHTML = "";
    pendingCanonical = null;
    collisionChoice = null;
    if (btnEditAfter) btnEditAfter.hidden = true;
    fileInput.value = "";
  }

  function showErrors(errors) {
    errorsBox.hidden = false;
    previewBox.hidden = true;
    errorList.innerHTML = "";
    (errors || []).forEach((msg) => {
      const li = document.createElement("li");
      li.textContent = msg;
      errorList.appendChild(li);
    });
  }

  function showWarnings(warnings) {
    if (!warnings || !warnings.length) {
      warningsBox.hidden = true;
      return;
    }
    warningsBox.hidden = false;
    warningList.innerHTML = "";
    warnings.forEach((msg) => {
      const li = document.createElement("li");
      li.textContent = msg;
      warningList.appendChild(li);
    });
  }

  function renderPreview(data) {
    const preview = data.preview || {};
    const sessions = preview.sessions || [];
    previewSummary.textContent =
      (preview.name || "Routine") +
      " · " +
      (preview.session_count || sessions.length) +
      " session(s) · schema " +
      (preview.schema_version || "?") +
      " · not saved yet";
    previewSessions.innerHTML = "";
    sessions.forEach((s) => {
      const li = document.createElement("li");
      const title = document.createElement("strong");
      title.textContent =
        (s.order != null ? "Day/Session " + s.order + ": " : "") +
        (s.name || s.id || "Session");
      const detail = document.createElement("p");
      detail.className = "instructions";
      const sourceExercises =
        (s.exercises && s.exercises.length
          ? s.exercises
          : (s.blocks || []).flatMap((b) => b.exercises || [])) || [];
      const exNames = sourceExercises
        .map((e) => {
          const metric =
            e.metric_kind === "reps" || e.metric_kind === "reps_per_side"
              ? (e.reps != null ? e.reps + " reps" : "reps")
              : e.duration_seconds
                ? e.duration_seconds + "s"
                : "metric";
          return (e.name || "Exercise") + " (" + metric + ")";
        })
        .join("; ");
      detail.textContent =
        (s.exercise_count || sourceExercises.length) +
        " exercise(s): " +
        (exNames || "—");
      li.append(title, detail);
      previewSessions.appendChild(li);
    });
    previewBox.hidden = false;

    pendingCanonical = data.canonical;
    const id = pendingCanonical && pendingCanonical.id;
    const exists = id && window.ERLibrary.getById(id);
    if (exists) {
      collisionPanel.hidden = false;
      collisionChoice = null;
      btnConfirm.disabled = true;
    } else {
      collisionPanel.hidden = true;
      collisionChoice = "new";
      btnConfirm.disabled = false;
    }
  }

  function clientGate(file) {
    const name = (file && file.name) || "";
    const lower = name.toLowerCase();
    if (!lower.endsWith(".json")) {
      return "Disallowed file extension — only .json import files are accepted.";
    }
    if (file.size > MAX_FILE_BYTES) {
      return (
        "File exceeds size limit of " +
        MAX_FILE_BYTES +
        " bytes (" +
        file.size +
        " bytes)."
      );
    }
    return null;
  }

  async function runValidateFile(file) {
    resetUi();
    setStatus("");
    const gate = clientGate(file);
    if (gate) {
      showErrors([gate]);
      setStatus(gate, "error");
      clearPreviewStore();
      return;
    }
    validating.hidden = false;
    setStatus("Validating…");
    let result;
    try {
      result = await validateFile(file);
    } catch (err) {
      validating.hidden = true;
      const msg = "Import validation failed in the browser. Library was not changed.";
      showErrors([msg, String(err && err.message ? err.message : err)]);
      setStatus(msg, "error");
      return;
    }
    validating.hidden = true;
    if (!result.ok) {
      showErrors(result.errors || ["Validation failed."]);
      showWarnings(result.warnings || []);
      setStatus("Import blocked — nothing saved.", "error");
      clearPreviewStore();
      return;
    }
    const canonical = adaptImportDocument(result.document);
    const data = {
      ok: true,
      preview: result.preview,
      canonical,
      warnings: result.warnings || [],
    };
    showWarnings(data.warnings);
    renderPreview(data);
    savePreviewStore({
      preview: data.preview,
      canonical: data.canonical,
      warnings: data.warnings,
      persisted: false,
    });
    setStatus("Preview ready — confirm to save to My routines.", "ok");
  }

  function confirmImport() {
    if (!pendingCanonical) return;
    const id = pendingCanonical.id;
    const exists = window.ERLibrary.getById(id);
    if (exists && !collisionChoice) {
      setStatus("Choose Replace or Import as copy before confirming.", "error");
      return;
    }
    let toSave = Object.assign({}, pendingCanonical, {
      updated_at: new Date().toISOString(),
    });
    if (exists && collisionChoice === "copy") {
      toSave.id = window.ERLibrary.newId();
      toSave.name = (toSave.name || "Routine") + " (copy)";
    }
    try {
      window.ERLibrary.upsert(toSave);
    } catch (err) {
      setStatus(
        "Save failed — preview kept; library unchanged. Retry when ready.",
        "error"
      );
      return;
    }
    clearPreviewStore();
    setStatus('Imported “' + (toSave.name || "routine") + "”.", "ok");
    if (btnEditAfter) {
      btnEditAfter.href = "/author.html?id=" + encodeURIComponent(toSave.id);
      btnEditAfter.hidden = false;
    }
    collisionPanel.hidden = true;
    btnConfirm.disabled = true;
    setTimeout(() => {
      window.location.href = "/library.html";
    }, 700);
  }

  function cancelImport() {
    clearPreviewStore();
    resetUi();
    setStatus("Import cancelled — library unchanged.", "ok");
  }

  btnChoose.addEventListener("click", () => fileInput.click());
  dropzone.addEventListener("click", (ev) => {
    if (ev.target === btnChoose) return;
    fileInput.click();
  });
  dropzone.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter" || ev.key === " ") {
      ev.preventDefault();
      fileInput.click();
    }
  });
  fileInput.addEventListener("change", () => {
    const f = fileInput.files && fileInput.files[0];
    if (f) runValidateFile(f);
  });
  ["dragenter", "dragover"].forEach((evt) => {
    dropzone.addEventListener(evt, (ev) => {
      ev.preventDefault();
      dropzone.classList.add("dropzone-active");
    });
  });
  ["dragleave", "drop"].forEach((evt) => {
    dropzone.addEventListener(evt, (ev) => {
      ev.preventDefault();
      dropzone.classList.remove("dropzone-active");
    });
  });
  dropzone.addEventListener("drop", (ev) => {
    const f =
      ev.dataTransfer && ev.dataTransfer.files && ev.dataTransfer.files[0];
    if (f) runValidateFile(f);
  });

  btnConfirm.addEventListener("click", confirmImport);
  btnCancel.addEventListener("click", cancelImport);
  if (btnRetry) {
    btnRetry.addEventListener("click", () => {
      resetUi();
      setStatus("Select another JSON file.");
      fileInput.click();
    });
  }
  if (btnReplace) {
    btnReplace.addEventListener("click", () => {
      collisionChoice = "replace";
      btnConfirm.disabled = false;
      setStatus("Will replace the existing routine on confirm.", "ok");
    });
  }
  if (btnCopy) {
    btnCopy.addEventListener("click", () => {
      collisionChoice = "copy";
      btnConfirm.disabled = false;
      setStatus("Will import as a new copy on confirm.", "ok");
    });
  }

  window.ERImport = {
    PREVIEW_KEY,
    MAX_BYTES: MAX_FILE_BYTES,
    clearPreviewStore,
    clientGate,
  };
}
