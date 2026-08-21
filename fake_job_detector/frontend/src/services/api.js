const API_BASE = 'http://localhost:8000/api';

export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    return await res.json();
  } catch (err) {
    return { status: 'offline', error: err.message };
  }
}

export async function fetchSamples() {
  const res = await fetch(`${API_BASE}/samples`);
  if (!res.ok) throw new Error('Failed to fetch samples');
  return await res.json();
}

export async function analyzeJob(payload) {
  const res = await fetch(`${API_BASE}/analyze-job`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Analysis request failed');
  }
  return await res.json();
}

export async function uploadBatchCSV(file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/analyze-batch`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || 'Batch analysis failed');
  }
  return await res.json();
}

export function getBatchDownloadUrl(downloadId) {
  return `${API_BASE}/download-batch/${downloadId}`;
}

export async function submitReport(reportData) {
  const res = await fetch(`${API_BASE}/report-job`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(reportData)
  });
  if (!res.ok) throw new Error('Failed to submit report');
  return await res.json();
}

export async function fetchReports(status = null) {
  const url = status ? `${API_BASE}/reports?status=${status}` : `${API_BASE}/reports`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch reports');
  return await res.json();
}

export async function verifyReport(reportId, decision, adminNotes = '') {
  const res = await fetch(`${API_BASE}/admin/verify-report`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      report_id: reportId,
      decision,
      admin_notes: adminNotes
    })
  });
  if (!res.ok) throw new Error('Verification failed');
  return await res.json();
}

export async function fetchModelInfo() {
  const res = await fetch(`${API_BASE}/model-info`);
  if (!res.ok) throw new Error('Failed to fetch model info');
  return await res.json();
}

export async function fetchModelVersions() {
  const res = await fetch(`${API_BASE}/model-versions`);
  if (!res.ok) throw new Error('Failed to fetch model versions');
  return await res.json();
}

export async function fetchModelComparison() {
  const res = await fetch(`${API_BASE}/model-versions/compare`);
  if (!res.ok) throw new Error('Failed to fetch model comparison');
  return await res.json();
}

export async function triggerRetrain(notes = '') {
  const res = await fetch(`${API_BASE}/admin/retrain`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ notes })
  });
  if (!res.ok) throw new Error('Retraining pipeline failed');
  return await res.json();
}

export async function fetchDashboardStats() {
  const res = await fetch(`${API_BASE}/dashboard/stats`);
  if (!res.ok) throw new Error('Failed to fetch dashboard stats');
  return await res.json();
}

export async function fetchThreatInsights() {
  const res = await fetch(`${API_BASE}/threat-insights`);
  if (!res.ok) throw new Error('Failed to fetch threat insights');
  return await res.json();
}
