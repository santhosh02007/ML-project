'use strict';
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const names = {inspector:'Job inspector',batch:'Batch analysis',history:'History & review',models:'Model lab',demo:'Demo Lab'};
let historyRows = [], samples = [], selected = '', metadata, activeRecord, batchRows = [];
const results = new Map(); let resultCounter = 0, toastTimer;
const pct = n => (n * 100).toFixed(1) + '%';
const date = s => s ? new Date(s).toLocaleString() : 'Not saved';
function notice(id, message) { $(id).textContent = message; $(id).hidden = !message; }
function toast(message) { clearTimeout(toastTimer); notice('toast', message); toastTimer = setTimeout(() => $('toast').hidden = true, 4500); }
async function api(path, options = {}) {
  const controller = new AbortController(); const timeout = setTimeout(() => controller.abort(), 90000);
  try {
    const response = await fetch(path, {...options, signal:controller.signal});
    const body = await response.json();
    if (!response.ok) {
      const detail = body.detail;
      throw new Error(Array.isArray(detail) ? detail.map(x => `${x.loc.slice(1).join(' ')}: ${x.msg}`).join('; ') : detail || 'The request could not be completed.');
    }
    return body;
  } catch (e) { if (e.name === 'AbortError') throw new Error('The request timed out. Refresh history before retrying a saved analysis.'); throw e; }
  finally { clearTimeout(timeout); }
}
const post = data => ({method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
function busy(button, state, label) { button.disabled = state; if (state) { button.dataset.label = button.textContent; button.textContent = label; } else button.textContent = button.dataset.label; }
function download(name, text, type) {
  const url = URL.createObjectURL(new Blob([text], {type})); const link = document.createElement('a');
  link.href = url; link.download = name; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function csvCell(value) {
  let text = String(value ?? ''); if (/^[\s]*[=+@-]|^[\t\r\n]/.test(text)) text = "'" + text;
  return '"' + text.replace(/"/g, '""') + '"';
}
function csvDownload(name, rows) { download(name, '\uFEFF' + rows.map(row => row.map(csvCell).join(',')).join('\r\n'), 'text/csv;charset=utf-8'); }
function resultHTML(r, printable = true) {
  const key = String(++resultCounter); results.set(key, r);
  const color = {High:'#bd4b52',Medium:'#aa7822',Low:'#348772'}[r.risk_level];
  const list = r.signals.rules.map(x => `<div class="signal warning"><strong>${esc(x.label)}</strong>${x.evidence.map(t => `<p>“${esc(t)}”</p>`).join('')}</div>`).join('') || '<p class="check-note">No explicit scam wording rules fired. This is not a safety guarantee.</p>';
  const tokens = (values, minus) => values.length ? values.map(t => `<span class="token ${minus ? 'minus' : ''}" title="LR contribution: ${esc(t.weight)}">${esc(t.term)}</span>`).join('') : '<span class="micro">No matching terms</span>';
  return `<article class="panel result-card"><div class="print-title"><h1>Veritas · Analysis report</h1></div><div class="result-top"><div><p class="eyebrow">${r.demo ? 'CLASSROOM EXAMPLE' : 'ANALYSIS RESULT'}</p><h2>${esc(r.verdict)}</h2><p>${esc(r.job.title)}</p><span class="badge ${esc(r.risk_level)}">${esc(r.risk_level)} concern</span></div><div class="score-ring" style="--score:${r.risk_score};--ring:${color}"><div class="score-inner"><strong>${r.risk_score}<small>/100</small></strong><span>Concern index</span></div></div></div><div class="result-body"><p class="recommendation">${esc(r.recommendation)}</p><section class="result-section"><h3>Two model perspectives</h3>${r.models.map(m => `<div class="model-line"><div><strong>${esc(m.name)}</strong>${m.champion ? '<span class="tag">PRIMARY</span>' : ''}<span>${m.score.toFixed(1)} / 100</span></div><div class="bar"><i style="width:${m.score}%"></i></div><p class="micro">${m.flagged ? 'Flagged' : 'Below threshold'} · threshold ${m.threshold.toFixed(0)} / 100</p></div>`).join('')}<p class="micro">Model scores estimate fraud signals. They are not verified probabilities.</p></section><section class="result-section"><h3>Wording to review</h3>${list}${r.signals.disclaimers.length ? `<div class="signal"><strong>Protective wording found</strong>${r.signals.disclaimers.map(x => `<p>${esc(x)}</p>`).join('')}<p class="micro">Warnings are treated separately from direct demands. Rules can still miss context.</p></div>` : ''}</section><section class="result-section"><h3>Contact & salary checks</h3>${[...r.signals.domain_notes,...r.signals.salary_notes].map(x => `<p class="check-note">${esc(x)}</p>`).join('')}</section><details class="result-section"><summary>Why the text influenced the model</summary><p class="micro">${esc(r.explanation.note)}</p><h4>Toward fraud</h4><div class="token-list">${tokens(r.explanation.toward_fraud,false)}</div><h4>Toward genuine</h4><div class="token-list">${tokens(r.explanation.toward_genuine,true)}</div><p class="micro">${r.vocabulary_terms} active vocabulary terms · ${r.analysis_ms} ms inference</p></details><details class="result-section"><summary>Posting analyzed</summary><p class="posting-text">${esc(r.job.description)}</p><p class="micro">${esc(r.job.company || 'Company not supplied')} · ${esc(r.job.contact_email || 'Email not supplied')} · ${esc(r.job.application_url || 'Website not supplied')}</p></details><p class="micro">${r.saved ? 'Saved locally · ' + esc(date(r.created_at)) : 'Not saved to history'} · Model v${esc(r.model_version)}</p><div class="result-actions"><button class="button secondary small" data-json="${key}">Download JSON ↓</button>${printable ? '<button class="button secondary small" data-print>Print / save PDF</button>' : ''}</div><p class="micro">${esc(r.notice)}</p></div></article>`;
}
function route() {
  const page = Object.hasOwn(names, location.hash.slice(1)) ? location.hash.slice(1) : 'inspector';
  document.querySelectorAll('.page').forEach(x => x.hidden = x.id !== 'page-' + page);
  document.querySelectorAll('[data-page]').forEach(x => { x.classList.toggle('active', x.dataset.page === page); if (x.dataset.page === page) x.setAttribute('aria-current','page'); else x.removeAttribute('aria-current'); });
  $('pageLabel').textContent = names[page]; document.title = `${names[page]} · Veritas`;
  $('sidebar').classList.remove('open'); $('scrim').hidden = true; $('menu').setAttribute('aria-expanded','false');
  if (page === 'history') loadHistory();
}
window.addEventListener('hashchange', route);
$('menu').onclick = () => { const open = $('sidebar').classList.toggle('open'); $('scrim').hidden = !open; $('menu').setAttribute('aria-expanded',String(open)); };
$('scrim').onclick = () => { $('sidebar').classList.remove('open'); $('scrim').hidden = true; $('menu').setAttribute('aria-expanded','false'); };
$('description').oninput = () => $('charCount').textContent = `${$('description').value.length.toLocaleString()} / 20,000`;
const emptyInspector = $('inspectResult').innerHTML;
$('inspectForm').addEventListener('reset', () => { $('inspectResult').innerHTML = emptyInspector; $('charCount').textContent = '0 / 20,000'; notice('inspectError',''); });
$('inspectForm').onsubmit = async e => {
  e.preventDefault(); notice('inspectError',''); busy($('analyzeButton'),true,'Analyzing…');
  try { const job = Object.fromEntries(new FormData(e.target)); job.save = $('saveHistory').checked; const result = await api('/api/analyze',post(job)); $('inspectResult').innerHTML = resultHTML(result); toast(result.saved ? 'Analysis saved to history.' : 'Analysis complete. Not saved.'); }
  catch (err) { notice('inspectError',err.message); } finally { busy($('analyzeButton'),false); }
};
document.addEventListener('click', e => {
  const json = e.target.closest('[data-json]'); if (json) download('veritas-analysis.json',JSON.stringify(results.get(json.dataset.json),null,2),'application/json');
  if (e.target.closest('[data-print]')) { document.body.classList.add(location.hash === '#demo' ? 'print-demo' : 'print-inspector'); window.print(); }
  const detail = e.target.closest('[data-record]'); if (detail) openRecord(detail.dataset.record);
});
window.addEventListener('afterprint', () => document.body.classList.remove('print-demo','print-inspector'));
$('batchForm').onsubmit = async e => {
  e.preventDefault(); const file = $('csvFile').files[0]; if (!file) return;
  if (file.size > 2 * 1024 * 1024) { notice('batchMessage','Choose a CSV smaller than 2 MB.'); return; }
  busy($('batchButton'),true,'Analyzing rows…'); notice('batchMessage','Processing your file. Please wait…');
  try {
    const body = new FormData(); body.append('file',file); const data = await api('/api/batch',{method:'POST',body}); batchRows = data.rows;
    notice('batchMessage',`${data.processed} of ${data.total} rows analyzed and saved. ${data.errors} invalid row(s).`);
    $('batchResult').innerHTML = `<section class="panel"><div class="panel-head"><h2>Batch results</h2><button id="exportBatch" class="button secondary small">Export results CSV ↓</button></div><div class="table-scroll"><table><thead><tr><th>CSV row</th><th>Job posting</th><th>Result</th><th>Details</th></tr></thead><tbody>${data.rows.map(row => `<tr><td>${row.row}</td><td>${esc(row.result?.job.title || row.title || 'Untitled')}</td><td>${row.result ? `<span class="badge ${row.result.risk_level}">${row.result.risk_level} · ${row.result.risk_score}/100</span>` : esc(row.error)}</td><td>${row.result ? `<button class="link-button" data-record="${esc(row.result.id)}">View →</button>` : 'Not saved'}</td></tr>`).join('')}</tbody></table></div></section>`;
    $('exportBatch').onclick = () => csvDownload('veritas-batch.csv',[['row','title','risk_level','concern_index','lr_score','rf_score','error'],...batchRows.map(x => [x.row,x.result?.job.title || x.title,x.result?.risk_level,x.result?.risk_score,...[0,1].map(i => x.result?.models[i]?.score),x.error || ''])]);
  } catch (err) { notice('batchMessage',err.message); } finally { busy($('batchButton'),false); }
};
function filteredHistory() { const q = $('historySearch').value.toLowerCase(); return historyRows.filter(r => `${r.title} ${r.company}`.toLowerCase().includes(q) && ($('riskFilter').value === 'all' || r.level === $('riskFilter').value) && ($('reviewFilter').value === 'all' || r.review === $('reviewFilter').value)); }
function renderHistory() {
  const rows = filteredHistory();
  $('historyStats').innerHTML = [['Total analyses',historyRows.length],['High concern',historyRows.filter(x => x.level === 'High').length],['Awaiting review',historyRows.filter(x => x.review === 'Pending').length],['Reviewed',historyRows.filter(x => x.review !== 'Pending').length]].map(([label,n]) => `<div class="stat"><span>${label}</span><strong>${n}</strong></div>`).join('');
  $('historyRows').innerHTML = rows.map(r => `<tr><td><strong>${esc(r.title)}</strong><small>${esc(r.company || 'Company not supplied')}</small></td><td>${esc(date(r.created_at))}</td><td><span class="badge ${esc(r.level)}">${esc(r.level)} · ${r.score}</span></td><td><span class="badge neutral">${esc(r.review)}</span></td><td><button class="link-button" data-record="${esc(r.id)}">View →</button></td></tr>`).join('') || '<tr><td colspan="5" class="empty">No matching analyses. Analyze a posting to create your first record.</td></tr>';
  $('historyCount').textContent = `${rows.length} of ${historyRows.length} saved analyses`; $('exportHistory').disabled = !rows.length;
}
async function loadHistory() { notice('historyError',''); try { historyRows = await api('/api/history'); renderHistory(); } catch (e) { notice('historyError', e.message); } }
$('refreshHistory').onclick = loadHistory;
['historySearch','riskFilter','reviewFilter'].forEach(id => $(id).addEventListener('input',renderHistory));
$('exportHistory').onclick = () => csvDownload('veritas-history.csv',[['title','company','analyzed_at','risk_level','concern_index','review','review_note'],...filteredHistory().map(r => [r.title,r.company,r.created_at,r.level,r.score,r.review,r.note])]);
async function openRecord(id) {
  try {
    const r = await api('/api/history/' + encodeURIComponent(id)); activeRecord = id; $('detailTitle').textContent = r.job.title;
    $('detailContent').innerHTML = resultHTML(r,false) + (r.review !== 'Pending' ? `<div class="review-box"><h3>${esc(r.review)}</h3><p>${esc(r.note)}</p><p class="micro">Reviewed ${esc(date(r.reviewed_at))}</p></div>` : '');
    $('reviewForm').hidden = r.review !== 'Pending'; $('reviewForm').reset(); notice('reviewError','');
    if (!$('detailDialog').open) $('detailDialog').showModal();
  } catch (e) { toast(e.message); }
}
$('closeDialog').onclick = () => $('detailDialog').close();
$('reviewForm').onsubmit = async e => {
  e.preventDefault(); busy($('reviewButton'),true,'Saving…'); notice('reviewError','');
  try { await api('/api/history/' + encodeURIComponent(activeRecord) + '/review', post({decision:$('decision').value,note:$('reviewNote').value})); await openRecord(activeRecord); await loadHistory(); toast('Review saved. Original prediction preserved.'); }
  catch (err) { notice('reviewError',err.message); } finally { busy($('reviewButton'),false); }
};
function selectScenario(id) {
  selected = id; const s = samples.find(x => x.id === id); if (!s) return;
  $('demoTitle').textContent = s.job.title; $('demoText').textContent = s.job.description; $('demoPurpose').textContent = s.purpose;
  $('demoResult').innerHTML = '<div class="empty">Run the analysis to see the model scores and evidence.</div>';
  document.querySelectorAll('[data-scenario]').forEach(x => { x.classList.toggle('active', x.dataset.scenario === id); x.setAttribute('aria-pressed',String(x.dataset.scenario === id)); });
}
$('scenarioList').onclick = e => { const b = e.target.closest('[data-scenario]'); if (b && !$('runDemo').disabled) selectScenario(b.dataset.scenario); };
$('runDemo').onsubmit = null;
$('runDemo').onclick = async () => {
  if (!selected) return; busy($('runDemo'),true,'Running models…');
  try { const r = await api('/api/demo/' + encodeURIComponent(selected),{method:'POST'}); $('demoResult').innerHTML = resultHTML(r); }
  catch (e) { $('demoResult').innerHTML = `<p class="notice error">${esc(e.message)}</p>`; } finally { busy($('runDemo'),false); }
};
function renderModels() {
  if (!metadata) return; const m = metadata, split = $('metricSplit').value;
  $('modelContent').innerHTML = `<div class="stats">${[['Dataset rows',m.raw_rows.toLocaleString()],['Usable rows',m.usable_rows.toLocaleString()],['TF-IDF features',m.features.toLocaleString()],['Split overlap',m.leakage_check.identical_description_group_overlap]].map(([l,n]) => `<div class="stat"><span>${l}</span><strong>${n}</strong></div>`).join('')}</div><div class="model-layout">${Object.entries(m.metrics).map(([key,value]) => { const v = value[split], cm = v.confusion_matrix; return `<section class="panel model-card"><p class="eyebrow">${m.champion === key ? 'PRIMARY · SELECTED ON VALIDATION F1' : 'COMPARISON MODEL'}</p><h2>${key === 'logistic_regression' ? 'Logistic Regression' : 'Random Forest'}</h2><div class="stats">${[['Fraud precision',v.precision],['Fraud recall',v.recall],['Fraud F1',v.f1]].map(([l,n]) => `<div class="stat"><span>${l}</span><strong>${pct(n)}</strong></div>`).join('')}</div><p class="micro">Accuracy: ${pct(v.accuracy)} · Average precision: ${pct(v.average_precision)} · Threshold: ${pct(value.threshold)}</p><h3>Confusion matrix</h3><p class="micro">Rows = actual label. Columns = predicted label.</p><table class="cm-table"><thead><tr><th>Actual ↓ / Predicted →</th><th>Genuine</th><th>Fraud</th></tr></thead><tbody><tr><th>Genuine</th><td class="correct">${cm[0][0]}<small>True negative</small></td><td>${cm[0][1]}<small>False alarm</small></td></tr><tr><th>Fraud</th><td>${cm[1][0]}<small>Missed fraud</small></td><td class="correct">${cm[1][1]}<small>True positive</small></td></tr></tbody></table></section>`; }).join('')}</div><section class="panel model-story"><h2>How the evaluation works</h2><p>${esc(m.method)}</p><div class="table-scroll"><table><thead><tr><th>Split</th><th>Total</th><th>Genuine</th><th>Fraud</th></tr></thead><tbody>${Object.entries(m.splits).map(([k,v]) => `<tr><td>${esc(k)}</td><td>${v.total}</td><td>${v.genuine}</td><td>${v.fraud}</td></tr>`).join('')}</tbody></table></div><p><b>Why fraud F1?</b> Most records are genuine. Accuracy alone can hide missed scams. Precision measures how many flags are correct; recall measures how many frauds are found; F1 balances both.</p><p><b>Leakage check:</b> ${esc(m.leakage_check.note)}</p><p><b>Data preparation:</b> ${m.removed_rows} short, conflicting or repeated full-text rows removed. Descriptions are grouped before splitting; the vocabulary is learned only from training rows.</p><p><b>What the concern index means:</b> It combines the primary ML score and local wording, domain and salary rules. Safety floors raise direct payment or secret-information requests. It is a project heuristic, separate from the model-only metrics above.</p><p class="notice">${esc(m.limitations)}</p><p class="micro">Dataset: <a href="https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction" target="_blank" rel="noopener noreferrer">Kaggle / EMSCAD job postings ↗</a> · Trained ${esc(date(m.trained_at))} · scikit-learn ${esc(m.sklearn_version)}</p></section>`;
}
$('metricSplit').onchange = renderModels;
async function init() {
  route();
  const tasks = await Promise.allSettled([api('/api/health'),api('/api/model-info'),api('/api/samples')]);
  if (tasks[0].status === 'fulfilled' && tasks[0].value.ready) { $('health').textContent = 'Models ready'; $('health').classList.add('ready'); }
  else { $('health').textContent = 'Connection unavailable'; notice('globalError','The local server is unavailable. Start the application and refresh this page.'); }
  if (tasks[1].status === 'fulfilled') { metadata = tasks[1].value; renderModels(); }
  else $('modelContent').innerHTML = '<p class="notice error">Model information could not be loaded. Refresh to retry.</p>';
  if (tasks[2].status === 'fulfilled') { samples = tasks[2].value; $('scenarioList').innerHTML = samples.map((s,i) => `<button class="scenario" data-scenario="${esc(s.id)}"><span>0${i+1}</span><div><strong>${esc(s.label)}</strong><small>${esc(s.purpose)}</small></div></button>`).join(''); if (samples.length) selectScenario(samples[0].id); }
  else { $('runDemo').disabled = true; $('scenarioList').textContent = 'Examples could not be loaded. Refresh to retry.'; }
}
init();
