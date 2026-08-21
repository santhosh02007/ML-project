/**
 * ==============================================================================================
 * FAKE JOB POSTING & RECRUITMENT SCAM DETECTOR - CLIENT APPLICATION CONTROLLER
 * Vanilla JavaScript (ES6+) with Real-Time Inference, SVG Gauge Animation, and Batch Processor
 * ==============================================================================================
 */

document.addEventListener("DOMContentLoaded", () => {
  initNavigation();
  initInspector();
  initBatchUploader();
  initAnalytics();
});

// ==============================================================================================
// 1. TAB NAVIGATION CONTROLLER
// ==============================================================================================
function initNavigation() {
  const tabBtns = document.querySelectorAll(".nav-tab-btn");
  const tabPanes = document.querySelectorAll(".tab-pane");

  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.dataset.tab;

      tabBtns.forEach((b) => b.classList.remove("active"));
      tabPanes.forEach((p) => p.classList.remove("active"));

      btn.classList.add("active");
      const targetPane = document.getElementById(targetId);
      if (targetPane) {
        targetPane.classList.add("active");
      }
    });
  });
}

// ==============================================================================================
// 2. LIVE SINGLE JOB INSPECTOR
// ==============================================================================================
function initInspector() {
  const form = document.getElementById("job-inspector-form");
  const clearBtn = document.getElementById("btn-clear-form");

  // Clear Button
  clearBtn.addEventListener("click", () => {
    form.reset();
    resetResultsView();
  });

  // Form Submit
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    triggerAnalysis();
  });
}

async function triggerAnalysis() {
  const submitBtn = document.getElementById("btn-analyze");
  const originalBtnHtml = submitBtn.innerHTML;

  const modelChoice = document.getElementById("field-model-select")
    ? document.getElementById("field-model-select").value
    : "logistic_regression";

  const payload = {
    title: document.getElementById("field-title").value,
    company_profile: document.getElementById("field-company-profile").value,
    description: document.getElementById("field-description").value,
    requirements: document.getElementById("field-requirements").value,
    benefits: document.getElementById("field-benefits").value,
    location: document.getElementById("field-location").value,
    employment_type: document.getElementById("field-employment-type").value,
    required_education: document.getElementById("field-education").value,
    required_experience: document.getElementById("field-experience").value,
    model: modelChoice,
  };

  if (!payload.title && !payload.description) {
    alert("Please provide at least a Job Title or Description.");
    return;
  }

  // Set Loading State
  submitBtn.disabled = true;
  submitBtn.innerHTML = `<span class="spinner"></span> Analyzing NLP Vectors...`;

  try {
    const response = await fetch("/api/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const result = await response.json();
    if (!response.ok) {
      alert(result.error || "Failed to analyze posting.");
      return;
    }

    renderResults(result);
  } catch (err) {
    console.error("Analysis Error:", err);
    alert("An error occurred while connecting to the inference server.");
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalBtnHtml;
  }
}

function renderResults(res) {
  const emptyState = document.getElementById("results-empty-state");
  const resultsContent = document.getElementById("results-content");

  emptyState.style.display = "none";
  resultsContent.style.display = "block";

  // Update Latency & Cache Badges
  const latencyBadge = document.getElementById("metric-latency-badge");
  const cacheBadge = document.getElementById("metric-cache-badge");
  if (latencyBadge && res.latency_ms !== undefined) {
    latencyBadge.innerText = `⚡ ${res.latency_ms}ms`;
  }
  if (cacheBadge) {
    cacheBadge.innerText = res.cached ? "⚡ Memory Cached" : "Fresh Inference";
    cacheBadge.style.color = res.cached ? "#a7f3d0" : "#a5b4fc";
  }

  // 1. Animate SVG Radial Gauge
  const fraudProb = res.fraud_probability; // 0.0 to 1.0
  const fraudPct = Math.round(fraudProb * 100);
  const gaugeFill = document.getElementById("gauge-fill");
  const gaugePctText = document.getElementById("gauge-pct-text");

  // Gauge circumference: 2 * PI * 80 ≈ 502.65
  const totalOffset = 502.65;
  const targetOffset = totalOffset - (totalOffset * fraudProb);

  gaugeFill.style.strokeDashoffset = targetOffset;
  gaugePctText.innerText = `${fraudPct}%`;

  // Color Interpolation for Gauge
  let strokeColor = "#10b981"; // Green (Genuine)
  if (fraudProb >= 0.70) {
    strokeColor = "#ef4444"; // Red (Scam)
  } else if (fraudProb >= 0.35) {
    strokeColor = "#f59e0b"; // Yellow (Suspicious)
  }
  gaugeFill.style.stroke = strokeColor;
  gaugePctText.style.color = strokeColor;

  // 2. Verdict Box
  const verdictBox = document.getElementById("verdict-box");
  const verdictHeading = document.getElementById("verdict-heading");
  const verdictSub = document.getElementById("verdict-sub");

  verdictBox.className = `verdict-box ${res.badge_class}`;
  verdictHeading.innerText = res.prediction;
  verdictSub.innerText = `Risk Assessment: ${res.risk_level} • Decision Engine: ${res.model_used}`;

  // 3. Mini Metrics
  document.getElementById("metric-fraud-prob").innerText = res.fraud_percentage;
  document.getElementById("metric-genuine-prob").innerText = res.genuine_percentage;
  document.getElementById("metric-word-count").innerText = res.cleaned_word_count;

  // 4. Rule Risk Alerts
  const ruleSection = document.getElementById("rule-alerts-section");
  const ruleContainer = document.getElementById("rule-alerts-container");
  ruleContainer.innerHTML = "";

  if (res.rule_alerts && res.rule_alerts.length > 0) {
    ruleSection.style.display = "block";
    res.rule_alerts.forEach((alert) => {
      const card = document.createElement("div");
      card.className = `rule-alert-card ${alert.level}`;
      const icon = alert.level === "critical" ? "🚨" : alert.level === "warning" ? "⚠️" : "ℹ️";
      card.innerHTML = `
        <div class="rule-alert-title">${icon} ${alert.title}</div>
        <div class="rule-alert-desc">${alert.desc}</div>
      `;
      ruleContainer.appendChild(card);
    });
  } else {
    ruleSection.style.display = "none";
  }

  // 5. Token Attribution Signals
  const scamTokensContainer = document.getElementById("scam-tokens-container");
  const genuineTokensContainer = document.getElementById("genuine-tokens-container");

  scamTokensContainer.innerHTML = "";
  genuineTokensContainer.innerHTML = "";

  if (res.scam_signals && res.scam_signals.length > 0) {
    res.scam_signals.forEach((sig) => {
      const badge = document.createElement("span");
      badge.className = "token-badge scam";
      badge.innerHTML = `⚠️ ${sig.token} <span class="token-weight">+${sig.weight}</span>`;
      scamTokensContainer.appendChild(badge);
    });
  } else {
    scamTokensContainer.innerHTML = `<span style="font-size:0.8rem; color:var(--text-dim);">No significant scam n-grams detected.</span>`;
  }

  if (res.genuine_signals && res.genuine_signals.length > 0) {
    res.genuine_signals.forEach((sig) => {
      const badge = document.createElement("span");
      badge.className = "token-badge genuine";
      badge.innerHTML = `✓ ${sig.token} <span class="token-weight">${sig.weight}</span>`;
      genuineTokensContainer.appendChild(badge);
    });
  } else {
    genuineTokensContainer.innerHTML = `<span style="font-size:0.8rem; color:var(--text-dim);">No strong corporate marker tokens found.</span>`;
  }
}

function resetResultsView() {
  document.getElementById("results-empty-state").style.display = "block";
  document.getElementById("results-content").style.display = "none";
}

// ==============================================================================================
// 3. BATCH CSV UPLOADER & TABLE VIEWER
// ==============================================================================================
function initBatchUploader() {
  const dropzone = document.getElementById("csv-dropzone");
  const fileInput = document.getElementById("csv-file-input");
  const batchResults = document.getElementById("batch-results-section");

  dropzone.addEventListener("click", () => fileInput.click());

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleBatchUpload(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleBatchUpload(e.target.files[0]);
    }
  });
}

async function handleBatchUpload(file) {
  if (!file.name.endsWith(".csv")) {
    alert("Please upload a valid .csv file.");
    return;
  }

  const modelChoice = document.getElementById("batch-model-select")
    ? document.getElementById("batch-model-select").value
    : "logistic_regression";

  const formData = new FormData();
  formData.append("file", file);
  formData.append("model", modelChoice);

  const dropzone = document.getElementById("csv-dropzone");
  dropzone.innerHTML = `<span class="spinner" style="width:32px; height:32px;"></span><p style="margin-top:1rem; font-weight:700;">Vectorizing & Scoring Postings in Memory...</p>`;

  try {
    const response = await fetch("/api/batch", {
      method: "POST",
      body: formData,
    });

    const res = await response.json();
    if (!response.ok) {
      alert(res.error || "Failed to process batch CSV.");
      resetDropzone();
      return;
    }

    renderBatchResults(res);
  } catch (err) {
    console.error("Batch Upload Error:", err);
    alert("An error occurred during batch processing.");
    resetDropzone();
  }
}

function resetDropzone() {
  const dropzone = document.getElementById("csv-dropzone");
  dropzone.innerHTML = `
    <div class="dropzone-icon">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="17 8 12 3 7 8"></polyline>
        <line x1="12" y1="3" x2="12" y2="15"></line>
      </svg>
    </div>
    <div class="dropzone-title">Click to upload or drag & drop CSV file</div>
    <div class="dropzone-sub">Supports standard Kaggle EMSCAD or raw job postings CSV files</div>
  `;
}

function renderBatchResults(data) {
  resetDropzone();
  const section = document.getElementById("batch-results-section");
  section.style.display = "block";

  // Update Speed Badge
  const speedBadge = document.getElementById("batch-speed-badge");
  if (speedBadge && data.latency_ms !== undefined) {
    speedBadge.style.display = "inline-block";
    speedBadge.innerText = `⚡ ${data.latency_ms}ms (${data.throughput_fps.toLocaleString()} rows/sec)`;
  }

  document.getElementById("batch-stat-total").innerText = data.total_records.toLocaleString();
  document.getElementById("batch-stat-fraud").innerText = data.fraud_count.toLocaleString();
  document.getElementById("batch-stat-genuine").innerText = data.genuine_count.toLocaleString();
  document.getElementById("batch-stat-rate").innerText = data.fraud_rate;

  const downloadBtn = document.getElementById("btn-download-batch");
  downloadBtn.href = data.download_url;

  // Render Table Rows
  const tbody = document.getElementById("batch-table-body");
  tbody.innerHTML = "";

  data.preview.forEach((row, idx) => {
    const tr = document.createElement("tr");

    let badgeClass = "badge-success";
    if (row.risk_level && row.risk_level.includes("HIGH")) badgeClass = "badge-danger";
    else if (row.risk_level && row.risk_level.includes("MODERATE")) badgeClass = "badge-warning";

    tr.innerHTML = `
      <td>${idx + 1}</td>
      <td><strong>${escapeHtml(row.title || "N/A")}</strong></td>
      <td>${escapeHtml(row.location || "N/A")}</td>
      <td><span class="table-badge ${badgeClass}">${escapeHtml(row.risk_level || "N/A")}</span></td>
      <td style="font-family:var(--font-mono); font-weight:700;">${(row.fraud_probability * 100).toFixed(1)}%</td>
    `;
    tbody.appendChild(tr);
  });
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ==============================================================================================
// 4. MODEL ANALYTICS & FEATURE IMPORTANCE
// ==============================================================================================
async function initAnalytics() {
  try {
    const response = await fetch("/api/metrics");
    const data = await response.json();
    if (!response.ok) return;

    // Populate Top 20 Fraud N-Grams
    const featureGrid = document.getElementById("feature-rank-grid");
    if (featureGrid && data.top_scam_features) {
      featureGrid.innerHTML = "";
      data.top_scam_features.forEach((item) => {
        const div = document.createElement("div");
        div.className = "feat-item";
        div.innerHTML = `
          <span class="feat-rank">#${item.rank}</span>
          <span class="feat-name">${item.feature}</span>
          <span class="feat-coef">+${item.coefficient.toFixed(2)}</span>
        `;
        featureGrid.appendChild(div);
      });
    }
  } catch (err) {
    console.error("Metrics load error:", err);
  }
}
