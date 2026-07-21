/**
 * MOD-ER-VISUALS — AD-021 / F-001: primary phone-glance instructions surface.
 * Visual media playback remains out of scope (no coming-soon / media placeholder).
 */
(function (global) {
  function renderVisual(panel, step) {
    if (!panel) return;
    panel.innerHTML = "";
    panel.classList.add("visual-panel--instructions", "instructions-panel");
    const text =
      (step && step.instructions && String(step.instructions).trim()) ||
      "Follow the on-screen cue for this step.";
    const p = document.createElement("p");
    p.id = "visual-caption";
    p.className = "step-instructions-text";
    p.textContent = text;
    panel.appendChild(p);
    panel.setAttribute("role", "region");
    panel.setAttribute("aria-label", "Current step instructions");
  }

  global.ERVisuals = { renderVisual };
})(window);
