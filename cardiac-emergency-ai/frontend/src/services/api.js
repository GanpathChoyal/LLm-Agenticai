/**
 * API service — centralized fetch helpers for Django backend
 */
const API_BASE = '';  // Vite proxy handles routing to Django

async function request(url, options = {}) {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function getDashboardData() {
  return request('/api/dashboard/');
}

export async function uploadPatientFiles(formData) {
  const res = await fetch('/upload/', {
    method: 'POST',
    body: formData,
  });
  return res;
}

export async function runPipeline(patientId) {
  return request(`/process/${patientId}/`);
}

export async function getReportData(reportId) {
  return request(`/api/report/${reportId}/`);
}

export async function confirmReport(reportId) {
  const formData = new FormData();
  formData.append('action', 'confirm');
  const res = await fetch(`/confirm/${reportId}/`, {
    method: 'POST',
    body: formData,
  });
  return res.json();
}
