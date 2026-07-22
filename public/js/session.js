/**
 * MOD-ER-SESSION — phase clock + controls (option_1 mobile).
 * Dual timeline: mirrors Python phase_machine expanders (AD-006).
 * U-01: duration owns done; reps are on-screen target.
 */
(function () {
  const TRANSITION_DEFAULT =
    typeof window.ER_TRANSITION_DEFAULT === "number"
      ? window.ER_TRANSITION_DEFAULT
      : 5;

  function transitionFor(ex) {
    if (ex.transition_seconds == null || ex.transition_seconds === "") {
      return TRANSITION_DEFAULT;
    }
    const n = Number(ex.transition_seconds);
    return Number.isFinite(n) && n >= 0 ? n : TRANSITION_DEFAULT;
  }

  function formatLoad(load) {
    if (!load) return null;
    if (load.kind === "bodyweight") return "Bodyweight";
    if (load.value == null) return load.kind || null;
    let text = String(load.value) + (load.unit ? " " + load.unit : "");
    if (load.per_hand) text += " / hand";
    if (load.holding_pattern) text += " (" + load.holding_pattern + ")";
    return text;
  }

  function sideSequence(ex) {
    const laterality = ex.laterality;
    const seq = ex.side_sequence || [];
    if (laterality === "both_sides_each_set") {
      return seq.length ? seq.slice() : ["left", "right"];
    }
    const kind = ex.metric_kind || "";
    if (
      (kind === "reps_per_side" || kind === "duration_per_side") &&
      !seq.length
    ) {
      return ["left", "right"];
    }
    return seq.length ? seq.slice() : null;
  }

  function workDurationReps(ex) {
    let duration =
      ex.duration_seconds != null && Number(ex.duration_seconds) > 0
        ? Number(ex.duration_seconds)
        : null;
    let reps =
      ex.reps != null && Number(ex.reps) > 0 ? Number(ex.reps) : null;
    if (ex.metric_kind === "rep_range" && reps == null && ex.max_reps != null) {
      reps = Number(ex.max_reps);
    }
    return { duration, reps };
  }

  function ownsDone(ex, duration, reps) {
    if (duration != null && duration > 0) return "duration";
    if (reps != null && reps > 0) return "reps_display_only";
    if (ex.metric_kind === "rep_range") return "reps_display_only";
    return "manual";
  }

  function joinTextList(value) {
    if (Array.isArray(value)) {
      return value
        .map(function (s) {
          return String(s).trim();
        })
        .filter(Boolean)
        .join("\n");
    }
    if (typeof value === "string") return value.trim();
    return "";
  }

  /** AD-021: prefer execution_instructions, else instructions, else technical_notes. */
  function resolveExerciseInstructions(ex, fallback) {
    const fromExec = joinTextList(ex && ex.execution_instructions);
    if (fromExec) return fromExec;
    if (ex && ex.instructions && String(ex.instructions).trim()) {
      return String(ex.instructions).trim();
    }
    const fromNotes = joinTextList(ex && ex.technical_notes);
    if (fromNotes) return fromNotes;
    return fallback || "";
  }

  function baseStep(opts) {
    const ex = opts.ex || {};
    const meta = opts.blockMeta || {};
    const duration = opts.duration;
    const reps = opts.reps;
    return {
      kind: opts.kind,
      exercise_index: opts.exIdx,
      exercise_id: ex.id,
      set: opts.setNum,
      sets_total: opts.setsTotal,
      name: opts.name,
      duration_seconds: duration,
      reps: reps,
      min_reps: ex.min_reps,
      max_reps: ex.max_reps,
      metric_kind: ex.metric_kind,
      instructions: opts.instructions || "",
      visual_url: ex.visual_url || null,
      owns_done:
        opts.kind === "exercise"
          ? ownsDone(ex, duration, reps)
          : duration
            ? "duration"
            : "manual",
      laterality: ex.laterality,
      side: opts.side || null,
      load: ex.load || null,
      load_display: formatLoad(ex.load),
      tempo: ex.tempo,
      block_id: meta.block_id,
      block_name: meta.block_name,
      block_index: meta.block_index,
      block_total: meta.block_total,
      block_type: meta.block_type,
      round: opts.roundNum != null ? opts.roundNum : null,
      rounds_total: opts.roundsTotal != null ? opts.roundsTotal : null,
    };
  }

  function appendWorkSides(steps, opts) {
    const ex = opts.ex;
    const { duration, reps } = workDurationReps(ex);
    const sides = sideSequence(ex);
    const name = ex.name || "Exercise " + (opts.exIdx + 1);
    const instructions = resolveExerciseInstructions(
      ex,
      "Work at a comfortable pace. Duration owns this step when set — reps are your target."
    );
    if (sides && sides.length) {
      sides.forEach((side) => {
        steps.push(
          baseStep({
            kind: "exercise",
            ex: ex,
            exIdx: opts.exIdx,
            setNum: opts.setNum,
            setsTotal: opts.setsTotal,
            name: name + " (" + side + ")",
            duration: duration,
            reps: reps,
            instructions: instructions,
            side: side,
            blockMeta: opts.blockMeta,
            roundNum: opts.roundNum,
            roundsTotal: opts.roundsTotal,
          })
        );
      });
    } else {
      steps.push(
        baseStep({
          kind: "exercise",
          ex: ex,
          exIdx: opts.exIdx,
          setNum: opts.setNum,
          setsTotal: opts.setsTotal,
          name: name,
          duration: duration,
          reps: reps,
          instructions: instructions,
          blockMeta: opts.blockMeta,
          roundNum: opts.roundNum,
          roundsTotal: opts.roundsTotal,
        })
      );
    }
  }

  function appendRest(steps, opts) {
    const seconds = Math.max(0, Number(opts.seconds) || 0);
    if (seconds <= 0) return;
    steps.push(
      baseStep({
        kind: "rest",
        ex: opts.ex || {},
        exIdx: opts.exIdx,
        setNum: opts.setNum,
        setsTotal: opts.setsTotal,
        name: "Rest",
        duration: seconds,
        reps: null,
        instructions: "Catch your breath. Next step follows.",
        blockMeta: opts.blockMeta,
        roundNum: opts.roundNum,
        roundsTotal: opts.roundsTotal,
      })
    );
  }

  function appendTransition(steps, opts) {
    const seconds = Number(opts.seconds);
    if (!Number.isFinite(seconds) || seconds <= 0) return;
    steps.push(
      baseStep({
        kind: "transition",
        ex: opts.ex || {},
        exIdx: opts.exIdx,
        setNum: opts.setNum,
        setsTotal: opts.setsTotal,
        name: opts.name || "Transition",
        duration: seconds,
        reps: null,
        instructions: "Get ready for the next step.",
        blockMeta: opts.blockMeta,
        roundNum: opts.roundNum,
        roundsTotal: opts.roundsTotal,
      })
    );
  }

  function annotateNext(steps) {
    let nextName = null;
    for (let i = steps.length - 1; i >= 0; i--) {
      steps[i].next_name = nextName;
      if (steps[i].kind === "exercise") nextName = steps[i].name;
    }
    return steps;
  }

  function buildTimelineFlat(exercises) {
    const steps = [];
    exercises.forEach((ex, exIdx) => {
      const sets = Math.max(1, Number(ex.sets) || 1);
      const restSeconds = Math.max(0, Number(ex.rest_seconds) || 0);
      const transitionSeconds = transitionFor(ex);
      for (let setNum = 1; setNum <= sets; setNum++) {
        const isLast =
          exIdx === exercises.length - 1 && setNum === sets;
        appendWorkSides(steps, {
          ex: ex,
          exIdx: exIdx,
          setNum: setNum,
          setsTotal: sets,
        });
        if (restSeconds > 0 && !isLast) {
          appendRest(steps, {
            seconds: restSeconds,
            ex: ex,
            exIdx: exIdx,
            setNum: setNum,
            setsTotal: sets,
          });
        }
        if (!isLast) {
          appendTransition(steps, {
            seconds: transitionSeconds,
            ex: ex,
            exIdx: exIdx,
            setNum: setNum,
            setsTotal: sets,
          });
        }
      }
    });
    return annotateNext(steps);
  }

  function appendBlockTransition(steps, block, blockMeta, isLastBlock) {
    if (isLastBlock) return;
    if (block.transition_after_block_seconds == null) return;
    const seconds = Math.max(0, Number(block.transition_after_block_seconds) || 0);
    if (seconds <= 0) return;
    const exercises = block.exercises || [];
    const ex = exercises.length ? exercises[exercises.length - 1] : { name: block.name };
    appendTransition(steps, {
      seconds: seconds,
      ex: ex,
      exIdx: Math.max(0, exercises.length - 1),
      setNum: 1,
      setsTotal: 1,
      blockMeta: blockMeta,
      name: "Block transition",
    });
  }

  function expandCircuit(steps, block, blockMeta, isLastBlock) {
    const exercises = block.exercises || [];
    const rounds = Math.max(1, Number(block.rounds) || 1);
    const restBetween = Math.max(
      0,
      Number(block.rest_between_rounds_seconds) || 0
    );
    for (let roundNum = 1; roundNum <= rounds; roundNum++) {
      exercises.forEach((ex, exIdx) => {
        const sets = Math.max(1, Number(ex.sets) || 1);
        for (let setNum = 1; setNum <= sets; setNum++) {
          appendWorkSides(steps, {
            ex: ex,
            exIdx: exIdx,
            setNum: setNum,
            setsTotal: sets,
            blockMeta: blockMeta,
            roundNum: roundNum,
            roundsTotal: rounds,
          });
          const restS = Math.max(0, Number(ex.rest_seconds) || 0);
          const isLastInRound =
            exIdx === exercises.length - 1 && setNum === sets;
          if (restS > 0 && !isLastInRound) {
            appendRest(steps, {
              seconds: restS,
              ex: ex,
              exIdx: exIdx,
              setNum: setNum,
              setsTotal: sets,
              blockMeta: blockMeta,
              roundNum: roundNum,
              roundsTotal: rounds,
            });
          }
          const trans = transitionFor(ex);
          if (!isLastInRound && trans > 0) {
            appendTransition(steps, {
              seconds: trans,
              ex: ex,
              exIdx: exIdx,
              setNum: setNum,
              setsTotal: sets,
              blockMeta: blockMeta,
              roundNum: roundNum,
              roundsTotal: rounds,
            });
          }
        }
      });
      if (roundNum < rounds && restBetween > 0) {
        const lastEx = exercises.length ? exercises[exercises.length - 1] : {};
        appendRest(steps, {
          seconds: restBetween,
          ex: lastEx,
          exIdx: Math.max(0, exercises.length - 1),
          setNum: 1,
          setsTotal: 1,
          blockMeta: blockMeta,
          roundNum: roundNum,
          roundsTotal: rounds,
        });
      }
    }
    appendBlockTransition(steps, block, blockMeta, isLastBlock);
  }

  function expandStraight(steps, block, blockMeta, isLastBlock) {
    const exercises = block.exercises || [];
    exercises.forEach((ex, exIdx) => {
      const sets = Math.max(1, Number(ex.sets) || 1);
      const restSeconds = Math.max(0, Number(ex.rest_seconds) || 0);
      const transitionSeconds = transitionFor(ex);
      for (let setNum = 1; setNum <= sets; setNum++) {
        const isLastExSet =
          exIdx === exercises.length - 1 && setNum === sets;
        appendWorkSides(steps, {
          ex: ex,
          exIdx: exIdx,
          setNum: setNum,
          setsTotal: sets,
          blockMeta: blockMeta,
          roundNum: 1,
          roundsTotal: 1,
        });
        if (restSeconds > 0 && !isLastExSet) {
          appendRest(steps, {
            seconds: restSeconds,
            ex: ex,
            exIdx: exIdx,
            setNum: setNum,
            setsTotal: sets,
            blockMeta: blockMeta,
            roundNum: 1,
            roundsTotal: 1,
          });
        } else if (restSeconds > 0 && isLastExSet && !isLastBlock) {
          appendRest(steps, {
            seconds: restSeconds,
            ex: ex,
            exIdx: exIdx,
            setNum: setNum,
            setsTotal: sets,
            blockMeta: blockMeta,
            roundNum: 1,
            roundsTotal: 1,
          });
        }
        if (!isLastExSet && transitionSeconds > 0) {
          appendTransition(steps, {
            seconds: transitionSeconds,
            ex: ex,
            exIdx: exIdx,
            setNum: setNum,
            setsTotal: sets,
            blockMeta: blockMeta,
            roundNum: 1,
            roundsTotal: 1,
          });
        }
      }
    });
    appendBlockTransition(steps, block, blockMeta, isLastBlock);
  }

  function expandPaired(steps, block, blockMeta, isLastBlock) {
    const exercises = block.exercises || [];
    if (exercises.length < 2) {
      expandStraight(steps, block, blockMeta, isLastBlock);
      return;
    }
    const a = exercises[0];
    const b = exercises[1];
    const rounds = Math.max(
      1,
      Number(block.rounds) ||
        Number(a.sets) ||
        Number(b.sets) ||
        1
    );
    const restBetween = block.rest_between_rounds_seconds;
    for (let roundNum = 1; roundNum <= rounds; roundNum++) {
      appendWorkSides(steps, {
        ex: a,
        exIdx: 0,
        setNum: roundNum,
        setsTotal: rounds,
        blockMeta: blockMeta,
        roundNum: roundNum,
        roundsTotal: rounds,
      });
      const aRest = Math.max(0, Number(a.rest_seconds) || 0);
      if (aRest > 0) {
        appendRest(steps, {
          seconds: aRest,
          ex: a,
          exIdx: 0,
          setNum: roundNum,
          setsTotal: rounds,
          blockMeta: blockMeta,
          roundNum: roundNum,
          roundsTotal: rounds,
        });
      }
      const aTrans = transitionFor(a);
      if (aTrans > 0) {
        appendTransition(steps, {
          seconds: aTrans,
          ex: a,
          exIdx: 0,
          setNum: roundNum,
          setsTotal: rounds,
          blockMeta: blockMeta,
          roundNum: roundNum,
          roundsTotal: rounds,
        });
      }
      appendWorkSides(steps, {
        ex: b,
        exIdx: 1,
        setNum: roundNum,
        setsTotal: rounds,
        blockMeta: blockMeta,
        roundNum: roundNum,
        roundsTotal: rounds,
      });
      if (roundNum < rounds) {
        const between =
          restBetween != null
            ? Math.max(0, Number(restBetween) || 0)
            : Math.max(0, Number(b.rest_seconds) || 0);
        if (between > 0) {
          appendRest(steps, {
            seconds: between,
            ex: b,
            exIdx: 1,
            setNum: roundNum,
            setsTotal: rounds,
            blockMeta: blockMeta,
            roundNum: roundNum,
            roundsTotal: rounds,
          });
        }
        const bTrans = transitionFor(b);
        if (bTrans > 0) {
          appendTransition(steps, {
            seconds: bTrans,
            ex: b,
            exIdx: 1,
            setNum: roundNum,
            setsTotal: rounds,
            blockMeta: blockMeta,
            roundNum: roundNum,
            roundsTotal: rounds,
          });
        }
      } else if (!isLastBlock) {
        const bRest = Math.max(0, Number(b.rest_seconds) || 0);
        if (bRest > 0 && restBetween == null) {
          appendRest(steps, {
            seconds: bRest,
            ex: b,
            exIdx: 1,
            setNum: roundNum,
            setsTotal: rounds,
            blockMeta: blockMeta,
            roundNum: roundNum,
            roundsTotal: rounds,
          });
        }
      }
    }
    appendBlockTransition(steps, block, blockMeta, isLastBlock);
  }

  function buildTimelineBlocks(blocks) {
    const steps = [];
    const ordered = blocks
      .slice()
      .sort((a, b) => (Number(a.order) || 0) - (Number(b.order) || 0));
    const total = ordered.length;
    ordered.forEach((block, bIdx) => {
      const blockMeta = {
        block_id: block.id,
        block_name: block.name,
        block_index: bIdx + 1,
        block_total: total,
        block_type: block.type,
      };
      const isLast = bIdx === total - 1;
      const btype = block.type || "sequence";
      if (btype === "circuit") expandCircuit(steps, block, blockMeta, isLast);
      else if (btype === "paired_sets")
        expandPaired(steps, block, blockMeta, isLast);
      else expandStraight(steps, block, blockMeta, isLast);
    });
    return annotateNext(steps);
  }

  function buildTimeline(routine) {
    const blocks = routine.blocks || [];
    if (blocks.length) return buildTimelineBlocks(blocks);
    return buildTimelineFlat(routine.exercises || []);
  }

  function formatTime(sec) {
    const s = Math.max(0, Math.ceil(sec));
    const m = Math.floor(s / 60);
    const r = s % 60;
    return m + ":" + String(r).padStart(2, "0");
  }

  const AUDIO_MUTE_KEY = "er_audio_muted";
  let audioCtx = null;
  let lastBeepRemaining = null;

  function isAudioMuted() {
    try {
      return localStorage.getItem(AUDIO_MUTE_KEY) === "1";
    } catch (e) {
      return false;
    }
  }

  function playCountdownBeep() {
    if (isAudioMuted()) return;
    try {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) return;
      if (!audioCtx) audioCtx = new Ctx();
      if (audioCtx.state === "suspended") audioCtx.resume();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.frequency.value = 880;
      osc.type = "sine";
      gain.gain.value = 0.08;
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.12);
    } catch (e) {
      /* Web Audio unavailable */
    }
  }

  function maybeBeepAtRemaining(remaining) {
    if (![1, 2, 3].includes(remaining)) return;
    if (lastBeepRemaining === remaining) return;
    lastBeepRemaining = remaining;
    playCountdownBeep();
  }

  function setWorkoutLockActive(active) {
    document.body.classList.toggle("session-workout-active", !!active);
  }

  function validateRoutine(routine) {
    const errors = [];
    const blocks = routine.blocks || [];
    const exercises = routine.exercises || [];
    if (!blocks.length && !exercises.length) {
      errors.push("Routine has no exercises.");
      return errors;
    }
    const list = blocks.length
      ? blocks.reduce((acc, b) => acc.concat(b.exercises || []), [])
      : exercises;
    list.forEach((ex) => {
      const d = Number(ex.duration_seconds);
      const r = Number(ex.reps);
      const minR = Number(ex.min_reps);
      const maxR = Number(ex.max_reps);
      const ok =
        (Number.isFinite(d) && d > 0) ||
        (Number.isFinite(r) && r > 0) ||
        (Number.isFinite(minR) && minR > 0) ||
        (Number.isFinite(maxR) && maxR > 0) ||
        ex.metric_kind === "rep_range";
      if (!ok) {
        errors.push(
          (ex.name || "Exercise") +
            ": add a duration and/or reps target before starting."
        );
      }
    });
    return errors;
  }

  const ui = {
    stage: document.getElementById("session-stage"),
    idle: document.getElementById("session-idle"),
    end: document.getElementById("session-end"),
    glance: document.getElementById("progress-glance"),
    totalBar: document.getElementById("session-total-bar"),
    totalElapsed: document.getElementById("total-elapsed"),
    label: document.getElementById("session-routine-label"),
    chip: document.getElementById("phase-chip"),
    heading: document.getElementById("exercise-heading"),
    timerValue: document.getElementById("timer-value"),
    timerLabel: document.getElementById("timer-label"),
    repsMeta: document.getElementById("reps-meta"),
    setMeta: document.getElementById("set-meta"),
    stepsMeta: document.getElementById("steps-meta"),
    visual: document.getElementById("visual-panel"),
    btnPause: document.getElementById("btn-pause"),
    btnContinue: document.getElementById("btn-continue"),
    btnSkip: document.getElementById("btn-skip"),
    btnBack: document.getElementById("btn-back"),
    btnRestart: document.getElementById("btn-restart"),
    btnEnd: document.getElementById("btn-end"),
    btnExtendRest: document.getElementById("btn-extend-rest"),
    progressBar: document.getElementById("progress-bar"),
    progressFill: document.getElementById("progress-fill"),
    progressCaption: document.getElementById("progress-caption"),
    endHeading: document.getElementById("end-heading"),
    endSummary: document.getElementById("end-summary"),
    endTotalLine: document.getElementById("end-total-line"),
    endProgress: document.getElementById("end-progress"),
  };

  if (!ui.stage || !window.ERLibrary) return;

  const state = {
    routine: null,
    steps: [],
    index: 0,
    remaining: 0,
    paused: false,
    timerId: null,
    started: false,
    countdownActive: false,
    liveTracking: null,
    // AD-022/AD-023: TOTAL wall-clock (independent of step Pause)
    totalElapsed: 0,
    totalRunning: false,
  };

  function clearTimer() {
    if (state.timerId) {
      clearInterval(state.timerId);
      state.timerId = null;
    }
  }

  function updateTotalDisplay() {
    if (ui.totalElapsed) {
      ui.totalElapsed.textContent = formatTime(state.totalElapsed);
    }
  }

  /** AD-022: start TOTAL only when first work/rest/transition begins (countdown excluded). */
  function ensureTotalStarted() {
    if (state.totalRunning || state.countdownActive) return;
    state.totalRunning = true;
  }

  function stopTotal() {
    state.totalRunning = false;
  }

  function resetTotal() {
    state.totalElapsed = 0;
    state.totalRunning = false;
    updateTotalDisplay();
  }

  function setPaused(paused) {
    state.paused = paused;
    ui.btnPause.hidden = paused;
    ui.btnContinue.hidden = !paused;
  }

  function displayPrefs() {
    const lt = state.liveTracking || {};
    return lt.display_preferences || {};
  }

  function allowExtendRest() {
    const lt = state.liveTracking || {};
    return lt.allow_extend_rest === true;
  }

  function restIncrement() {
    const lt = state.liveTracking || {};
    const n = Number(lt.rest_extension_increment_seconds);
    return Number.isFinite(n) && n > 0 ? n : 15;
  }

  function renderStep() {
    if (state.countdownActive) {
      ui.chip.textContent = "Starting";
      ui.chip.className = "phase-chip phase-chip--countdown";
      ui.heading.textContent = "Get ready";
      ui.timerLabel.textContent = "Starting in";
      ui.timerValue.textContent = formatTime(state.remaining);
      const countdownMsg =
        "First work step starts when the countdown reaches zero. You can wait or skip ahead.";
      if (window.ERVisuals) {
        window.ERVisuals.renderVisual(ui.visual, { instructions: countdownMsg });
      }
      ui.repsMeta.innerHTML = "<strong>Reps target</strong> —";
      ui.setMeta.innerHTML = "<strong>Set</strong> —";
      ui.stepsMeta.innerHTML =
        "<strong>Steps left</strong> " + state.steps.length;
      if (ui.btnExtendRest) ui.btnExtendRest.hidden = true;
      if (window.ERProgress && ui.glance) {
        const first = state.steps[0] || {};
        window.ERProgress.updateGlance(
          { root: ui.glance },
          {
            block_name: first.block_name,
            block_index: first.block_index,
            next_name: first.name,
          },
          displayPrefs()
        );
      }
      return;
    }

    const step = state.steps[state.index];
    if (!step) {
      finish(false);
      return;
    }
    ui.chip.className =
      "phase-chip" +
      (step.kind === "rest"
        ? " phase-chip--rest"
        : step.kind === "transition"
          ? " phase-chip--transition"
          : "");
    ui.chip.textContent =
      step.kind === "exercise"
        ? "Exercise"
        : step.kind === "rest"
          ? "Rest"
          : "Transition";
    ui.heading.textContent = step.name;
    const stepInstructions =
      step.instructions ||
      (step.kind === "exercise"
        ? "Work at a comfortable pace. Duration owns this step when set — reps are your target."
        : "");
    if (step.metric_kind === "rep_range" && step.min_reps != null) {
      ui.repsMeta.innerHTML =
        "<strong>Reps target</strong> " +
        step.min_reps +
        "–" +
        (step.max_reps != null ? step.max_reps : step.reps);
    } else if (step.reps != null) {
      ui.repsMeta.innerHTML = "<strong>Reps target</strong> " + step.reps;
    } else {
      ui.repsMeta.innerHTML = "<strong>Reps target</strong> —";
    }
    if (step.kind === "exercise") {
      ui.setMeta.innerHTML =
        "<strong>Set</strong> " + step.set + " of " + step.sets_total;
    } else {
      ui.setMeta.innerHTML = "<strong>Set</strong> —";
    }
    const left = Math.max(0, state.steps.length - state.index - 1);
    ui.stepsMeta.innerHTML = "<strong>Steps left</strong> " + left;

    if (step.duration_seconds != null && step.duration_seconds > 0) {
      ui.timerLabel.textContent =
        step.kind === "rest" ? "Rest remaining" : "Time remaining";
      ui.timerValue.textContent = formatTime(state.remaining);
    } else {
      ui.timerLabel.textContent = "Reps target — advance when ready";
      ui.timerValue.textContent =
        step.reps != null ? String(step.reps) + " reps" : "—";
    }

    if (ui.btnExtendRest) {
      const showExtend = step.kind === "rest" && allowExtendRest();
      ui.btnExtendRest.hidden = !showExtend;
      if (showExtend) {
        const inc = restIncrement();
        ui.btnExtendRest.textContent = "+" + inc;
        ui.btnExtendRest.title = "Extend rest +" + inc + "s";
        ui.btnExtendRest.setAttribute(
          "aria-label",
          "Extend rest by " + inc + " seconds"
        );
      }
    }

    if (window.ERVisuals) {
      window.ERVisuals.renderVisual(ui.visual, {
        instructions: stepInstructions,
        name: step.name,
      });
    }
    if (window.ERProgress) {
      window.ERProgress.updateProgress(
        {
          bar: ui.progressBar,
          fill: ui.progressFill,
          caption: ui.progressCaption,
        },
        state.index,
        state.steps.length,
        false
      );
      if (ui.glance) {
        window.ERProgress.updateGlance(
          { root: ui.glance },
          step,
          displayPrefs()
        );
      }
    }
  }

  function tick() {
    // AD-023: TOTAL keeps advancing while Pause freezes only the step timer.
    if (state.totalRunning) {
      state.totalElapsed += 1;
      updateTotalDisplay();
    }
    if (state.paused) return;
    if (state.countdownActive) {
      state.remaining -= 1;
      maybeBeepAtRemaining(state.remaining);
      ui.timerValue.textContent = formatTime(state.remaining);
      if (state.remaining <= 0) {
        state.countdownActive = false;
        loadStep(0);
      }
      return;
    }
    const step = state.steps[state.index];
    if (!step) return;
    if (step.duration_seconds != null && step.duration_seconds > 0) {
      state.remaining -= 1;
      maybeBeepAtRemaining(state.remaining);
      ui.timerValue.textContent = formatTime(state.remaining);
      if (state.remaining <= 0) {
        advance(1);
      }
    }
  }

  function startTimer() {
    clearTimer();
    state.timerId = setInterval(tick, 1000);
  }

  function loadStep(index) {
    state.index = Math.max(0, Math.min(index, state.steps.length));
    if (state.index >= state.steps.length) {
      finish(false);
      return;
    }
    const step = state.steps[state.index];
    state.remaining =
      step.duration_seconds != null && step.duration_seconds > 0
        ? step.duration_seconds
        : 0;
    lastBeepRemaining = null;
    setPaused(false);
    // AD-022: first work/rest/transition after countdown starts TOTAL
    ensureTotalStarted();
    renderStep();
    startTimer();
  }

  function advance(delta) {
    if (state.countdownActive) {
      state.countdownActive = false;
      loadStep(0);
      return;
    }
    loadStep(state.index + delta);
  }

  function finish(endedEarly) {
    clearTimer();
    stopTotal();
    state.started = false;
    state.countdownActive = false;
    setWorkoutLockActive(false);
    ui.stage.hidden = true;
    if (ui.glance) ui.glance.hidden = true;
    if (ui.totalBar) ui.totalBar.hidden = true;
    ui.idle.hidden = true;
    ui.end.hidden = false;
    const totalStr = formatTime(state.totalElapsed);
    const doneIndex = endedEarly ? state.index : state.steps.length;
    const prog = window.ERProgress
      ? window.ERProgress.updateProgress(
          {
            bar: ui.progressBar,
            fill: ui.progressFill,
            caption: ui.progressCaption,
          },
          doneIndex,
          state.steps.length,
          endedEarly
        )
      : { caption: "" };
    ui.endHeading.textContent = endedEarly ? "Session ended" : "Session complete";
    const routineName =
      state.routine && state.routine.name ? state.routine.name : "routine";
    ui.endSummary.textContent = endedEarly
      ? "You ended early. Progress is saved on this screen — restart anytime from My routines."
      : "Nice work. You finished the guided session for “" + routineName + "”.";
    if (ui.endTotalLine) {
      ui.endTotalLine.hidden = false;
      ui.endTotalLine.textContent = "Total session time: " + totalStr + ".";
    }
    ui.endProgress.textContent = prog.caption;
    window.ERLibrary.clearActiveRoutine();
  }

  function startCountdownThenWork() {
    const lt = state.liveTracking || {};
    const n = Number(lt.countdown_before_start_seconds);
    if (Number.isFinite(n) && n > 0) {
      state.countdownActive = true;
      state.remaining = n;
      setPaused(false);
      renderStep();
      startTimer();
      return;
    }
    state.countdownActive = false;
    loadStep(0);
  }

  function begin(routine) {
    const errors = validateRoutine(routine);
    if (errors.length) {
      ui.idle.hidden = false;
      ui.stage.hidden = true;
      ui.end.hidden = true;
      if (ui.glance) ui.glance.hidden = true;
      if (ui.totalBar) ui.totalBar.hidden = true;
      ui.label.textContent = errors[0];
      return;
    }
    state.routine = routine;
    state.liveTracking = routine.live_tracking || null;
    state.steps = buildTimeline(routine);
    state.started = true;
    resetTotal();
    ui.label.textContent =
      (routine.name || "Routine") + " · from saved routine";
    ui.idle.hidden = true;
    ui.end.hidden = true;
    ui.stage.hidden = false;
    if (ui.glance) ui.glance.hidden = false;
    if (ui.totalBar) ui.totalBar.hidden = false;
    setWorkoutLockActive(true);
    lastBeepRemaining = null;
    startCountdownThenWork();
  }

  ui.btnPause.addEventListener("click", () => {
    if (!state.started) return;
    setPaused(true);
  });
  ui.btnContinue.addEventListener("click", () => {
    if (!state.started) return;
    setPaused(false);
  });
  ui.btnSkip.addEventListener("click", () => {
    if (!state.started) return;
    advance(1);
  });
  ui.btnBack.addEventListener("click", () => {
    if (!state.started) return;
    if (state.countdownActive) return;
    advance(-1);
  });
  ui.btnRestart.addEventListener("click", () => {
    if (!state.routine) return;
    begin(state.routine);
  });
  ui.btnEnd.addEventListener("click", () => {
    if (!state.started) return;
    finish(true);
  });
  if (ui.btnExtendRest) {
    ui.btnExtendRest.addEventListener("click", () => {
      if (!state.started || state.countdownActive) return;
      const step = state.steps[state.index];
      if (!step || step.kind !== "rest" || !allowExtendRest()) return;
      const inc = restIncrement();
      state.remaining += inc;
      ui.timerValue.textContent = formatTime(state.remaining);
    });
  }

  function showDayPicker(routine) {
    const picker = document.getElementById("session-day-picker");
    const select = document.getElementById("session-day-select");
    const startBtn = document.getElementById("btn-start-picked-day");
    if (!picker || !select || !window.ERLibrary.sortedSessions) {
      const flat = window.ERLibrary.flattenForRunner
        ? window.ERLibrary.flattenForRunner(routine)
        : routine;
      begin(flat);
      return;
    }
    const sessions = window.ERLibrary.sortedSessions(routine);
    if (sessions.length <= 1) {
      picker.hidden = true;
      const flat = window.ERLibrary.flattenForRunner(routine);
      begin(flat);
      return;
    }
    ui.idle.hidden = true;
    ui.stage.hidden = true;
    ui.end.hidden = true;
    if (ui.glance) ui.glance.hidden = true;
    if (ui.totalBar) ui.totalBar.hidden = true;
    picker.hidden = false;
    select.innerHTML = "";
    sessions.forEach((s) => {
      const opt = document.createElement("option");
      opt.value = s.id;
      opt.textContent =
        (s.order != null ? "Day " + s.order + ": " : "") + (s.name || s.id);
      select.appendChild(opt);
    });
    const startPicked = () => {
      const flat = window.ERLibrary.flattenForRunner(routine, select.value);
      picker.hidden = true;
      begin(flat);
    };
    startBtn.onclick = startPicked;
  }

  document.addEventListener("DOMContentLoaded", () => {
    const id = window.ERLibrary.getActiveRoutineId();
    if (!id) return;
    const routine = window.ERLibrary.getById(id);
    if (!routine) {
      ui.label.textContent =
        "Saved routine not found in this browser. Pick one from My routines.";
      return;
    }
    const preferred = window.ERLibrary.getActiveSessionId
      ? window.ERLibrary.getActiveSessionId()
      : null;
    const sessions = window.ERLibrary.sortedSessions
      ? window.ERLibrary.sortedSessions(routine)
      : [];
    if (preferred || sessions.length <= 1) {
      const flat = window.ERLibrary.flattenForRunner
        ? window.ERLibrary.flattenForRunner(routine, preferred)
        : routine;
      begin(flat);
      return;
    }
    showDayPicker(routine);
  });

  window.ERSession = {
    buildTimeline,
    validateRoutine,
    TRANSITION_DEFAULT,
    transitionFor,
  };
})();
