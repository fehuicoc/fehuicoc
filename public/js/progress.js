/**
 * MOD-ER-PROGRESS — glanceable strip + bar (option_1 / AD-007, AD-017).
 */
(function (global) {
  function updateProgress(ui, stepIndex, total, endedEarly) {
    const pct =
      total <= 0 ? 0 : Math.min(100, Math.round((stepIndex / total) * 100));
    if (ui.bar) {
      ui.bar.setAttribute("aria-valuenow", String(pct));
    }
    if (ui.fill) {
      ui.fill.style.width = pct + "%";
    }
    let caption;
    if (total <= 0) caption = "No steps";
    else if (endedEarly)
      caption =
        "Ended early · completed " + stepIndex + " of " + total + " steps";
    else if (stepIndex >= total)
      caption = "Complete · " + total + " of " + total + " steps";
    else caption = "Step " + (stepIndex + 1) + " of " + total + " · In progress";
    if (ui.caption) ui.caption.textContent = caption;
    return { percent: pct, caption };
  }

  function formatLoad(load) {
    if (!load) return "—";
    if (load.kind === "bodyweight") return "Bodyweight";
    if (load.value == null) return load.kind || "—";
    let text = String(load.value) + (load.unit ? " " + load.unit : "");
    if (load.per_hand) text += " / hand";
    if (load.holding_pattern) text += " (" + load.holding_pattern + ")";
    return text;
  }

  function updateGlance(ui, step, prefs) {
    if (!ui || !ui.root) return;
    const show = prefs || {};
    const blockLabel =
      step && step.block_name
        ? (step.block_index != null
            ? step.block_index + " · " + step.block_name
            : step.block_name)
        : "—";
    const roundLabel =
      step && step.round != null && step.rounds_total != null
        ? step.round + " of " + step.rounds_total
        : "—";
    const setLabel =
      step && step.kind === "exercise" && step.set != null
        ? step.set +
          (step.sets_total != null ? " of " + step.sets_total : "")
        : step && step.set != null
          ? String(step.set)
          : "—";
    const sideLabel =
      step && step.side
        ? String(step.side).charAt(0).toUpperCase() +
          String(step.side).slice(1)
        : "—";
    const loadLabel =
      (step && (step.load_display || formatLoad(step.load))) || "—";
    const nextLabel = (step && step.next_name) || "—";

    function setCell(id, value, visible) {
      const el = ui.root.querySelector('[data-glance="' + id + '"]');
      if (!el) return;
      const val = el.querySelector(".value");
      if (val) val.textContent = value;
      el.hidden = visible === false;
    }

    setCell("block", blockLabel, show.show_block_progress !== false);
    setCell("round", roundLabel, true);
    setCell(
      "set",
      setLabel,
      show.show_current_set !== false || show.show_total_sets !== false
    );
    setCell("side", sideLabel, show.show_side !== false);
    setCell("load", loadLabel, show.show_load !== false);
    setCell("next", nextLabel, show.show_next_exercise !== false);
  }

  global.ERProgress = { updateProgress, updateGlance, formatLoad };
})(window);
