"use strict";

const API = "/api/bolton-connect";
// Demonstration role. A real deployment would use an authenticated session.
const HEADERS = { "X-Demo-Role": "staff", "Content-Type": "application/json" };

const FLAG_LABELS = {
  clarification_required: "Needs more info",
  unverified_or_caveated_recommendation: "Unverified / caveated recommendation",
  health_or_disability_support: "Health or disability support",
};

function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k === "class") node.className = v;
    else node.setAttribute(k, v);
  }
  for (const child of [].concat(children)) {
    if (child == null) continue;
    node.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
  }
  return node;
}

function showAuthError(msg) {
  const box = document.getElementById("auth-error");
  box.textContent = msg;
  box.classList.remove("hidden");
}

async function api(path, options = {}) {
  const res = await fetch(API + path, { headers: HEADERS, ...options });
  if (res.status === 403) {
    showAuthError("This view requires the adviser (staff) role.");
    throw new Error("forbidden");
  }
  if (!res.ok) throw new Error(`Request failed (${res.status}).`);
  return res.json();
}

async function loadStats() {
  const stats = await api("/stats");
  const grid = document.getElementById("stats");
  grid.textContent = "";
  const cells = [
    ["Total cases", stats.total_cases],
    ["Needing review", stats.cases_needing_review],
    ["Sessions saved", stats.sessions_saved],
  ];
  Object.entries(stats.by_status || {}).forEach(([k, v]) => cells.push([`Status: ${k}`, v]));
  cells.forEach(([label, n]) => {
    grid.appendChild(el("div", { class: "stat" }, [el("div", { class: "n" }, String(n)), el("div", {}, label)]));
  });
}

function flagBadges(flags) {
  const wrap = el("span", {});
  (flags || []).forEach((f) => {
    wrap.appendChild(el("span", { class: "badge demo" }, FLAG_LABELS[f] || f));
    wrap.appendChild(document.createTextNode(" "));
  });
  return wrap;
}

async function loadCases() {
  const body = document.getElementById("cases-body");
  body.textContent = "";
  const { cases } = await api("/cases");
  if (!cases.length) {
    body.appendChild(el("tr", {}, [el("td", { colspan: "5" }, "No cases yet. Share a plan from the resident view to create one.")]));
    return;
  }
  cases.forEach((c) => {
    const btn = el("button", { class: "secondary", type: "button" }, "Open");
    btn.addEventListener("click", () => openCase(c.id));
    body.appendChild(el("tr", {}, [
      el("td", { "data-label": "Created" }, c.created_at),
      el("td", { "data-label": "Status" }, el("span", { class: "status status-" + c.status }, c.status)),
      el("td", { "data-label": "Summary" }, c.summary || ""),
      el("td", { "data-label": "Flags" }, flagBadges(c.flags)),
      el("td", { "data-label": "Action" }, btn),
    ]));
  });
}

function openCase(caseId) {
  api(`/cases/${caseId}`).then(renderDetail).catch(() => {});
}

function renderDetail(c) {
  const body = document.getElementById("detail-body");
  body.textContent = "";

  const overview = el("div", { class: "detail-overview" });
  body.appendChild(overview);
  overview.appendChild(el("p", {}, [el("strong", {}, "Reference: "), c.id]));
  overview.appendChild(el("p", {}, [el("strong", {}, "Summary: "), c.summary || ""]));
  overview.appendChild(el("p", {}, [el("strong", {}, "Flags: ")]));
  overview.appendChild(flagBadges(c.flags));

  if ((c.flags || []).includes("unverified_or_caveated_recommendation")) {
    overview.appendChild(el("div", { class: "caveat" }, "This case includes recommendations that are unverified or carry a caveat. Confirm availability and eligibility before offering them to the resident."));
  }

  // Status controls
  const statusSel = el("select", { id: "status-sel", "aria-label": "Case status" });
  ["new", "in_review", "actioned", "closed"].forEach((s) => {
    const opt = el("option", { value: s }, s);
    if (s === c.status) opt.setAttribute("selected", "selected");
    statusSel.appendChild(opt);
  });
  const assignInput = el("input", { type: "text", id: "assign-input", placeholder: "Assign to (optional)", "aria-label": "Assign to" });
  if (c.assigned_to) assignInput.value = c.assigned_to;
  const saveBtn = el("button", { class: "primary", type: "button" }, "Update case");
  saveBtn.addEventListener("click", async () => {
    await api(`/cases/${c.id}`, { method: "PATCH", body: JSON.stringify({ status: statusSel.value, assigned_to: assignInput.value || null }) });
    await loadStats();
    await loadCases();
    openCase(c.id);
  });
  const controls = el("div", { class: "detail-controls" }, [el("h3", {}, "Update")]);
  controls.appendChild(el("label", { for: "status-sel" }, "Status"));
  controls.appendChild(statusSel);
  controls.appendChild(el("label", { for: "assign-input" }, "Assigned to"));
  controls.appendChild(assignInput);
  controls.appendChild(el("div", { class: "actions" }, [saveBtn]));
  body.appendChild(controls);

  // Notes
  const notesSection = el("div", { class: "detail-notes" });
  body.appendChild(notesSection);
  notesSection.appendChild(el("h3", {}, "Notes"));
  const notes = el("ul", { class: "plain" });
  (c.notes || []).forEach((n) => notes.appendChild(el("li", {}, `[${n.author_role}] ${n.note} — ${n.created_at}`)));
  if (!(c.notes || []).length) notes.appendChild(el("li", {}, "No notes yet."));
  notesSection.appendChild(notes);

  const noteInput = el("textarea", { id: "note-input", "aria-label": "Add a note", maxlength: "2000" });
  const addBtn = el("button", { class: "secondary", type: "button" }, "Add note");
  addBtn.addEventListener("click", async () => {
    const text = noteInput.value.trim();
    if (!text) return;
    await api(`/cases/${c.id}/notes`, { method: "POST", body: JSON.stringify({ note: text }) });
    openCase(c.id);
  });
  notesSection.appendChild(el("label", { for: "note-input" }, "Add a note"));
  notesSection.appendChild(noteInput);
  notesSection.appendChild(el("div", { class: "actions" }, [addBtn]));

  const detail = document.getElementById("detail");
  detail.classList.remove("hidden");
  detail.focus();
  detail.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function init() {
  try {
    await loadStats();
    await loadCases();
  } catch (_) {
    /* auth error already surfaced */
  }
}

init();
