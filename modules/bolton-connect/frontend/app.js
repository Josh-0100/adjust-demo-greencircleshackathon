"use strict";

const API = "/api/bolton-connect";

const PROVENANCE = {
  resident_stated: { text: "You told us", cls: "resident" },
  verified: { text: "Verified", cls: "verified" },
  official_source: { text: "Official source", cls: "official" },
  ai_suggestion: { text: "AI suggestion", cls: "ai" },
  synthetic_demo: { text: "Demonstration", cls: "demo" },
};

let lastPlan = null;

function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k === "class") node.className = v;
    else if (k === "html") node.innerHTML = v; // only for trusted static strings
    else node.setAttribute(k, v);
  }
  for (const child of [].concat(children)) {
    if (child == null) continue;
    node.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
  }
  return node;
}

function badge(provenance) {
  const p = PROVENANCE[provenance] || PROVENANCE.ai_suggestion;
  return el("span", { class: "badge " + p.cls }, p.text);
}

function planItemList(items) {
  const ul = el("ul", { class: "plain" });
  items.forEach((it) => {
    const li = el("li", {}, [it.text, " ", badge(it.provenance)]);
    if (it.source_url) {
      li.appendChild(document.createTextNode(" "));
      li.appendChild(el("a", { href: it.source_url, target: "_blank", rel: "noopener" }, "link"));
    }
    ul.appendChild(li);
  });
  return ul;
}

function section(title, bodyNode, id) {
  const wrap = el("div", { class: "plan-section", ...(id ? { id } : {}) }, [el("h3", {}, title)]);
  wrap.appendChild(bodyNode);
  return wrap;
}

function renderService(rec) {
  const stateClass = "elig " + rec.eligibility_state;
  const card = el("div", { class: "service" }, [
    el("h4", {}, [rec.name, " ", el("span", { class: stateClass }, rec.eligibility_label)]),
    el("p", { class: "meta" }, `${rec.provider} · ${rec.category.replaceAll("_", " ")}`),
    el("p", {}, rec.why_it_helps),
  ]);
  if (rec.reasons && rec.reasons.length) {
    card.appendChild(el("p", { class: "meta" }, "Why this was suggested:"));
    const ul = el("ul", { class: "plain" });
    rec.reasons.forEach((r) => ul.appendChild(el("li", {}, r)));
    card.appendChild(ul);
  }
  if (rec.missing_information && rec.missing_information.length) {
    const box = el("div", { class: "missing" }, [el("strong", {}, "Still to check: ")]);
    box.appendChild(document.createTextNode(rec.missing_information.join("; ")));
    card.appendChild(box);
  }
  if (rec.next_steps && rec.next_steps.length) {
    card.appendChild(el("p", { class: "meta" }, "Next steps:"));
    const ul = el("ul", { class: "plain" });
    rec.next_steps.forEach((s) => ul.appendChild(el("li", {}, s)));
    card.appendChild(ul);
  }
  (rec.caveats || []).forEach((c) => {
    card.appendChild(el("div", { class: "caveat" }, c));
  });
  if (!rec.auto_recommended) {
    card.appendChild(el("div", { class: "caveat" }, "Not an automatic recommendation — please confirm this is right for you with an adviser."));
  }
  return card;
}

function renderPathway(p) {
  const wrap = el("div", { class: "service" }, [
    el("h4", {}, "Towards: " + p.target_sector),
    el("p", { class: "meta" }, "Skills you may already have: " + (p.current_skills.join(", ") || "—")),
    el("p", { class: "meta" }, "Skills that could help: " + (p.skill_gaps.join(", ") || "—")),
  ]);
  if (p.training.length) {
    wrap.appendChild(el("p", { class: "meta" }, "Training ideas:"));
    const ul = el("ul", { class: "plain" });
    p.training.forEach((t) => {
      const li = el("li", {}, [t.title + " (" + t.provider + ") ", badge(t.source.synthetic ? "synthetic_demo" : "official_source")]);
      if (t.source.url) li.appendChild(el("a", { href: t.source.url, target: "_blank", rel: "noopener" }, " link"));
      ul.appendChild(li);
    });
    wrap.appendChild(ul);
  }
  if (p.opportunities.length) {
    wrap.appendChild(el("p", { class: "meta" }, "Example roles (demonstration only):"));
    const ul = el("ul", { class: "plain" });
    p.opportunities.forEach((o) => ul.appendChild(el("li", {}, [o.title, " ", badge("synthetic_demo")])));
    wrap.appendChild(ul);
  }
  (p.caveats || []).forEach((c) => wrap.appendChild(el("div", { class: "caveat" }, c)));
  return wrap;
}

function renderUnderstanding(a) {
  const rows = [
    ["Work situation", a.employment_status.replaceAll("_", " ")],
    ["Experience", a.experience.join(", ")],
    ["Skills you stated", a.skills.join(", ")],
    ["Goals", a.goals.join(", ")],
    ["Things that make work harder", a.barriers.join(", ")],
    ["Training interests", a.training_interests.join(", ")],
  ].filter(([, v]) => v);
  const ul = el("ul", { class: "plain" });
  rows.forEach(([k, v]) => ul.appendChild(el("li", {}, [el("strong", {}, k + ": "), v])));
  return section("What we understood from your words", ul);
}

function renderPlan(resp) {
  lastPlan = resp;
  const a = resp.assessment;
  const body = document.getElementById("result-body");
  body.textContent = "";

  // Clarification path: too little information to help responsibly.
  if (a.clarification_required) {
    body.appendChild(el("div", { class: "notice" }, [
      el("strong", {}, "We need a little more to help. "),
      a.clarifying_question || "Could you tell us a bit more about your situation?",
    ]));
    body.appendChild(el("p", {}, "Add some detail above and create your plan again."));
    reveal();
    return;
  }

  body.appendChild(el("div", { class: "plan-brand" }, [
    el("img", { class: "brand-logo", src: "assets/adjust-logo.png", alt: "Adjust", width: "1354", height: "390" }),
    el("span", {}, "Adjust AI · Resident Support"),
  ]));
  body.appendChild(el("p", { class: "plan-meta" }, [
    el("strong", {}, resp.plan.resident_name + "'s plan"),
    ` · ${resp.plan.borough} · generated ${resp.plan.generated_at} · method: ${resp.plan.provider}`,
  ]));
  body.appendChild(el("div", { class: "notice" }, resp.plan.disclaimer));

  const key = el("div", { class: "key" }, [
    "Labels:", badge("resident_stated"), badge("verified"), badge("official_source"), badge("ai_suggestion"), badge("synthetic_demo"),
  ]);
  body.appendChild(key);

  body.appendChild(renderUnderstanding(a));
  body.appendChild(section("Your goals", planItemList(resp.plan.goals)));
  body.appendChild(section("Your strengths", planItemList(resp.plan.strengths)));
  if (resp.plan.barriers.length) body.appendChild(section("Things that make work harder right now", planItemList(resp.plan.barriers)));

  const services = el("div", { class: "service-grid" });
  resp.plan.recommended_services.forEach((r) => services.appendChild(renderService(r)));
  body.appendChild(section("Suggested support services", services.childElementCount ? services : el("p", {}, "No services matched yet — an adviser can help."), "local-services"));

  if (resp.plan.training_opportunities.length) body.appendChild(section("Training ideas", planItemList(resp.plan.training_opportunities), "training"));

  if (resp.plan.employment_exploration.length) {
    const paths = el("div", { class: "service-grid" });
    resp.plan.employment_exploration.forEach((p) => paths.appendChild(renderPathway(p)));
    body.appendChild(section("Exploring employment", paths, "employment-pathways"));
  }

  body.appendChild(section("Things to do soon", planItemList(resp.plan.immediate_next_steps)));
  body.appendChild(section("Longer-term ideas", planItemList(resp.plan.longer_term_milestones)));
  body.appendChild(section("People who can help", planItemList(resp.plan.human_support_contacts), "human-support"));

  if (resp.session_id) {
    const url = `${location.origin}${location.pathname}?session=${resp.session_id}`;
    body.appendChild(el("div", { class: "notice" }, [
      el("strong", {}, "Saved. "), "Come back any time with this private link: ",
      el("a", { href: url }, url),
    ]));
  }
  if (resp.case_id) {
    body.appendChild(el("div", { class: "notice" }, [
      el("strong", {}, "Shared with an adviser. "),
      "Your reference is " + resp.case_id + ". A person will review your plan.",
    ]));
  }

  reveal();
}

function reveal() {
  const result = document.getElementById("result");
  result.classList.remove("hidden");
  result.focus();
  result.scrollIntoView({ behavior: "smooth", block: "start" });
}

function buildPayload(form) {
  const v = (id) => form.querySelector(id).value.trim();
  const checked = (id) => form.querySelector(id).checked;
  const profile = { borough: "Bolton" };
  if (v("#age_band")) profile.age_band = v("#age_band");
  if (v("#employment_status")) profile.employment_status = v("#employment_status");
  if (v("#digital_confidence")) profile.digital_confidence = v("#digital_confidence");
  if (checked("#health")) profile.has_health_condition_or_disability = true;
  if (checked("#benefits")) profile.receives_benefits = true;
  return {
    text: v("#text"),
    profile,
    resident_name: v("#name") || "Resident",
    consent_save: checked("#consent_save"),
    consent_share: checked("#consent_share"),
  };
}

async function onSubmit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const errorBox = document.getElementById("form-error");
  const btn = document.getElementById("submit-btn");
  errorBox.classList.add("hidden");

  const payload = buildPayload(form);
  if (payload.text.length < 10) {
    errorBox.textContent = "Please write at least a sentence about your situation.";
    errorBox.classList.remove("hidden");
    return;
  }

  btn.disabled = true;
  btn.textContent = "Creating your plan…";
  try {
    const res = await fetch(`${API}/plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      throw new Error(detail.detail || `Something went wrong (${res.status}).`);
    }
    renderPlan(await res.json());
  } catch (err) {
    errorBox.textContent = err.message || "Sorry, we couldn't create your plan. Please try again.";
    errorBox.classList.remove("hidden");
  } finally {
    btn.disabled = false;
    btn.textContent = "Create my plan";
  }
}

async function resumeFromLink() {
  const params = new URLSearchParams(location.search);
  const sessionId = params.get("session");
  if (!sessionId) return;
  try {
    const res = await fetch(`${API}/sessions/${encodeURIComponent(sessionId)}`);
    if (!res.ok) return;
    const session = await res.json();
    if (session.result) {
      // Stored result is a full ActionPlan; wrap it for the renderer.
      renderPlan({ assessment: planAssessmentFallback(session.result), plan: session.result, session_id: sessionId });
    }
  } catch (_) {
    /* ignore */
  }
}

// The saved result stores the ActionPlan; reconstruct a minimal assessment view.
function planAssessmentFallback(plan) {
  return {
    employment_status: "unknown",
    experience: [], skills: [], goals: [], barriers: [], support_needs: [],
    training_interests: [], support_preferences: [],
    clarification_required: false, clarifying_question: null,
  };
}

function onPrint() { window.print(); }

function onDownload() {
  if (!lastPlan) return;
  const blob = new Blob([JSON.stringify(lastPlan.plan, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = el("a", { href: url, download: "adjust-resident-plan.json" });
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

document.getElementById("assess-form").addEventListener("submit", onSubmit);
document.getElementById("print-btn").addEventListener("click", onPrint);
document.getElementById("download-btn").addEventListener("click", onDownload);
resumeFromLink();
