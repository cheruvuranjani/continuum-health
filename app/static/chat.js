const API_URL = window.CONTINUUM_API_URL;

const CITIES = {
  "San Francisco, CA": [37.7749, -122.4194],
  "Oakland, CA":       [37.8044, -122.2712],
  "San Jose, CA":      [37.3382, -121.8863],
  "Los Angeles, CA":   [34.0522, -118.2437],
};

const STEPS = {
  urgency:   ["Step 1 of 5 — Urgency",    20],
  symptoms:  ["Step 2 of 5 — Symptoms",   40],
  emergency: ["Emergency",               100],
  care_type: ["Step 3 of 5 — Care type",  60],
  insurance: ["Step 4 of 5 — Insurance",  80],
  city:      ["Step 5 of 5 — Location",   90],
  routing:   ["Finding care...",          95],
  result:    ["Care pathway resolved",   100],
};

const EMERGENCY_SYMS = [
  "Chest pain",
  "Difficulty breathing",
  "Severe bleeding",
  "Loss of consciousness"
];

const OTHER_SYMS = ["Fever", "Sore throat", "Cough", "Rash", "Other"];

let ans          = {};
let selectedSyms = new Set();


function setProgress(step) {
  const [label, pct] = STEPS[step] || ["", 0];
  document.getElementById("prog-label").textContent = label;
  document.getElementById("prog-fill").style.width  = pct + "%";
  document.getElementById("prog-wrap").style.display =
    step === "routing" ? "none" : "block";
}

function msg(role, text) {
  const d = document.createElement("div");
  d.className = "msg" + (role === "u" ? " u" : "");
  d.innerHTML = `
    <div class="av ${role === "u" ? "u" : ""}">${role === "u" ? "You" : "C"}</div>
    <div class="bub ${role === "u" ? "u" : ""}">${text}</div>
  `;
  document.getElementById("msgs").appendChild(d);
  d.scrollIntoView({ behavior: "smooth", block: "end" });
}

function clear() {
  document.getElementById("actions").innerHTML = "";
  selectedSyms = new Set();
}

function restartLink() {
  const btn       = document.createElement("button");
  btn.className   = "restart-link";
  btn.textContent = "Start over";
  btn.onclick     = restart;
  document.getElementById("actions").appendChild(btn);
}

function pills(opts, showRestart = true) {
  const w     = document.createElement("div");
  w.className = "pills";

  opts.forEach(o => {
    const b       = document.createElement("button");
    b.className   = "pill-btn" + (o.cls ? " " + o.cls : "");
    b.textContent = o.label;
    b.onclick     = () => {
      w.querySelectorAll(".pill-btn").forEach(x => {
        x.disabled      = true;
        x.style.opacity = "0.45";
      });
      b.classList.add("sel");
      b.style.opacity = "1";
      const rl = document.querySelector(".restart-link");
      if (rl) rl.style.display = "none";
      msg("u", o.label);
      setTimeout(() => o.fn(), 300);
    };
    w.appendChild(b);
  });

  document.getElementById("actions").appendChild(w);
  if (showRestart) restartLink();
}

function showSymptoms() {
  msg("bot", "What are your symptoms? Select all that apply.");

  const card     = document.createElement("div");
  card.className = "sym-card";
  card.innerHTML = `
    <div class="sym-section danger">
      Emergency — select if applicable
    </div>
    <div class="pills">
      ${EMERGENCY_SYMS.map(s => `
        <button class="pill-btn danger"
                data-sym="${s}"
                onclick="toggleSym(this,'emergency')">${s}</button>
      `).join("")}
    </div>
    <div class="sym-divider"></div>
    <div class="sym-section">Other symptoms</div>
    <div class="pills">
      ${OTHER_SYMS.map(s => `
        <button class="pill-btn"
                data-sym="${s}"
                onclick="toggleSym(this,'other')">${s}</button>
      `).join("")}
    </div>
    <div id="fever-wrap" style="display:none; margin-top:10px">
      <div class="sym-section" style="margin-bottom:8px">
        Is the fever above 102°F?
      </div>
      <div class="pills">
        <button class="pill-btn danger"
                onclick="ans.feverHigh=true; markFever(this)">
          Yes — above 102°F
        </button>
        <button class="pill-btn"
                onclick="ans.feverHigh=false; markFever(this)">
          No — below 102°F
        </button>
      </div>
    </div>
    <button class="continue-btn" onclick="submitSymptoms()">Continue</button>
  `;

  document.getElementById("actions").appendChild(card);
  restartLink();
}

function markFever(btn) {
  btn.classList.add(btn.classList.contains("danger") ? "sel-danger" : "sel");
  btn.parentNode.querySelectorAll(".pill-btn").forEach(b => {
    b.disabled      = true;
    b.style.opacity = "0.45";
  });
  btn.style.opacity = "1";
}

function toggleSym(btn, type) {
  const sym = btn.dataset.sym;
  if (selectedSyms.has(sym)) {
    selectedSyms.delete(sym);
    btn.classList.remove("sel", "sel-danger");
  } else {
    selectedSyms.add(sym);
    btn.classList.add(type === "emergency" ? "sel-danger" : "sel");
  }
  if (sym === "Fever") {
    document.getElementById("fever-wrap").style.display =
      selectedSyms.has("Fever") ? "block" : "none";
  }
}

function submitSymptoms() {
  const emergSel = [...selectedSyms].filter(s => EMERGENCY_SYMS.includes(s));

  if (emergSel.length > 0) {
    msg("u", emergSel.join(", "));
    go("emergency");
    return;
  }

  if (selectedSyms.has("Fever") && ans.feverHigh === true) {
    msg("u", "Fever above 102°F");
    ans.urgency = "urgent";
    msg("bot",
      "With a fever above 102°F, please go to urgent care immediately. " +
      "Finding the nearest urgent care — I will notify you when your spot is secured."
    );
    go("insurance");
    return;
  }

  const other = [...selectedSyms].filter(s => OTHER_SYMS.includes(s));
  msg("u", other.length > 0 ? other.join(", ") : "General symptoms");
  go("care_type");
}

async function callAPI() {
  const city       = ans.city || "San Francisco, CA";
  const [lat, lng] = CITIES[city] || [37.7749, -122.4194];
  const specialty  = ans.urgency === "urgent" ? "urgent_care" : "primary_care";
  const insurance  = (ans.insurance || "uninsured").toLowerCase();

  const resp = await fetch(API_URL + "/api/v1/route", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ lat, lng, specialty, insurance, radius_miles: 15 })
  });
  return resp.json();
}

function renderResult(data) {
  clear();
  document.getElementById("prog-wrap").style.display = "block";
  setProgress("result");

  const actions = document.getElementById("actions");

  if (!data || !data.resolved) {
    actions.innerHTML = `
      <div class="emerg-card">
        <p>Unable to find care. Please call your insurance provider.</p>
        <div class="pills" style="margin-top:10px">
          <button class="pill-btn" onclick="restart()">Start over</button>
        </div>
      </div>`;
    return;
  }

  const hasProviders = (data.primary_care && data.primary_care.length > 0) ||
                       (data.urgent_care  && data.urgent_care.length  > 0);

  if (!hasProviders) {
    actions.innerHTML = `
      <div class="result-card">
        <p style="font-size:13px;color:#666;line-height:1.6">
          No providers found within 15 miles of your location.
          Try a different city or contact your insurance provider.
        </p>
        <div class="pills" style="margin-top:10px">
          <button class="pill-btn" onclick="restart()">Try again</button>
        </div>
      </div>`;
    return;
  }

  let html  = `<div class="result-card">`;
  html     += `<div class="mttr">Resolved in ${data.mttr_seconds}s</div>`;

  if (data.primary_care && data.primary_care.length > 0) {
    html += `<div class="rsec">Primary care — ${ans.insurance || ""} network</div>`;
    data.primary_care.forEach(p => {
      const slots = (p.slots || []).filter(s => s.available);
      html += `
        <div class="prow">
          <div>
            <div class="pname">${p.name}</div>
            <div class="paddr">${p.address}</div>
          </div>
          <div>
            <div class="pdist">${p.distance_miles} mi</div>
            ${slots.length > 0
              ? `<div class="pslot">Next: ${slots[0].datetime.substring(11, 16)}</div>`
              : ""}
          </div>
        </div>`;
    });
  }

  if (data.urgent_care && data.urgent_care.length > 0) {
    html += `<div class="rsec">Urgent care</div>`;
    data.urgent_care.forEach(u => {
      html += `
        <div class="prow">
          <div>
            <div class="pname">${u.name}</div>
            <div class="paddr">${u.address}</div>
          </div>
          <div class="pdist">${u.distance_miles} mi</div>
        </div>`;
    });
  }

  if (data.pharmacy) {
    const p = data.pharmacy;
    html   += `<div class="rsec">Nearest pharmacy</div>`;
    html   += `
      <div class="prow">
        <div>
          <div class="pname">${p.name}</div>
          <div class="paddr">${p.address}</div>
        </div>
        <div class="pdist">${p.is_open_24h ? "Open 24hr" : "Check hours"}</div>
      </div>`;
  }

  html += `
    <div class="tag-wrap">
      <span class="tag">${ans.care_type || "Adult"}</span>
      <span class="tag">${ans.city || "San Francisco, CA"}</span>
      <span class="tag">${ans.insurance || "Uninsured"}</span>
    </div>
    <div class="pills">
      <button class="pill-btn primary" onclick="requestBooking()">Request booking</button>
      <button class="pill-btn" onclick="restart()">Start over</button>
    </div>
  </div>`;

  actions.innerHTML = html;
}

function requestBooking() {
  msg("u", "Request booking");
  document.getElementById("actions").innerHTML = `
    <div class="confirm-card">
      <p>Your appointment request has been submitted.
         You will receive a confirmation shortly.</p>
      <br>
      <p>If your condition worsens before your appointment,
         <strong>call 911 or go to your nearest ER.</strong></p>
      <div class="pills" style="margin-top:12px">
        <button class="pill-btn" onclick="restart()">Start over</button>
      </div>
    </div>`;
}

function showRunner() {
  document.getElementById("actions").innerHTML = `
    <div class="runner-wrap">
      <i class="ti ti-run runner-icon" aria-hidden="true"></i>
      <div class="runner-track"></div>
      <div class="runner-text">Routing across your provider network...</div>
    </div>`;
}

function restart() {
  ans          = {};
  selectedSyms = new Set();
  document.getElementById("msgs").innerHTML          = "";
  document.getElementById("prog-wrap").style.display = "block";
  clear();
  go("urgency");
}

async function go(step) {
  clear();
  setProgress(step);

  if (step === "urgency") {
    msg("bot", "How can I help you today?");
    pills([
      { label: "Urgent: I need care now", fn: () => {
          ans.urgency = "urgent";
          msg("bot", "I understand. Let me ask a few quick questions.");
          go("symptoms");
      }},
      { label: "Primary care: can wait", fn: () => {
          ans.urgency = "primary";
          msg("bot", "Got it. Let me help you find the right care.");
          go("care_type");
      }}
    ], false);

  } else if (step === "symptoms") {
    showSymptoms();

  } else if (step === "emergency") {
    document.getElementById("actions").innerHTML = `
      <div class="emerg-card">
        <h3>This may be a medical emergency</h3>
        <p>Please call <strong>911</strong> or go to your nearest
           <strong>Emergency Room</strong> immediately.
           Do not drive yourself. Ask someone to call 911 now.
           <strong>Do not wait for an appointment.</strong></p>
        <div class="pills">
          <button class="pill-btn danger"
                  onclick="window.open('tel:911')">Call 911</button>
          <button class="pill-btn"
                  onclick="window.open('https://www.google.com/maps/search/emergency+room+near+me')">
            Find nearest ER
          </button>
          <button class="pill-btn" onclick="restart()">Start over</button>
        </div>
      </div>`;

  } else if (step === "care_type") {
    msg("bot", "Who needs care?");
    pills([
      { label: "Adult",     fn: () => { ans.care_type = "Adult";     go("insurance"); }},
      { label: "Pediatric", fn: () => { ans.care_type = "Pediatric"; go("insurance"); }},
      { label: "Senior",    fn: () => { ans.care_type = "Senior";    go("insurance"); }},
    ]);

  } else if (step === "insurance") {
    msg("bot",
      "What insurance do you have? " +
      "This determines which provider network we search."
    );
    pills([
      { label: "HealthFirst HMO", fn: () => { ans.insurance = "healthfirst"; go("city"); }},
      { label: "MedConnect PPO",  fn: () => { ans.insurance = "medconnect";  go("city"); }},
      { label: "CareShield PPO",  fn: () => { ans.insurance = "careshield";  go("city"); }},
      { label: "UnityHealth PPO", fn: () => { ans.insurance = "unityhealth"; go("city"); }},
      { label: "ClearPath PPO",   fn: () => { ans.insurance = "clearpath";   go("city"); }},
      { label: "Uninsured",       fn: () => { ans.insurance = "uninsured";   go("city"); }},
    ]);

  } else if (step === "city") {
    msg("bot", "Where are you located?");
    pills(Object.keys(CITIES)
      .map(c => ({ label: c, fn: () => { ans.city = c; go("routing"); }}))
    );

  } else if (step === "routing") {
    msg("bot", "Finding the best care option for you...");
    showRunner();
    try {
      const data = await callAPI();
      renderResult(data);
    } catch (e) {
      clear();
      document.getElementById("prog-wrap").style.display = "block";
      document.getElementById("actions").innerHTML = `
        <div class="emerg-card">
          <p>Error connecting to API. Make sure the API server is running.</p>
          <div class="pills" style="margin-top:8px">
            <button class="pill-btn" onclick="restart()">Try again</button>
          </div>
        </div>`;
    }
  }
}

go("urgency");
