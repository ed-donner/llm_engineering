const API_BASE = "/api";

async function fetchJSON(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: "Unknown error" }));
    throw new Error(error.error || `HTTP ${response.status}`);
  }
  return response.json();
}

const api = {
  datasets: {
    list: () => fetchJSON(`${API_BASE}/datasets`),
    get: (id) => fetchJSON(`${API_BASE}/datasets/${id}`),
    create: (data) => fetchJSON(`${API_BASE}/datasets`, { method: "POST", body: JSON.stringify(data) }),
    delete: (id) => fetch(`${API_BASE}/datasets/${id}`, { method: "DELETE" }),
    getRecords: (id, page = 1, limit = 100) =>
      fetchJSON(`${API_BASE}/datasets/${id}/records?page=${page}&limit=${limit}`),
  },

  models: {
    list: () => fetchJSON(`${API_BASE}/models`),
  },

  generate: {
    start: (data) => fetchJSON(`${API_BASE}/generate`, { method: "POST", body: JSON.stringify(data) }),
    status: (runId) => fetchJSON(`${API_BASE}/generate/${runId}`),
  },

  templates: {
    list: () => fetchJSON(`${API_BASE}/templates`),
    get: (id) => fetchJSON(`${API_BASE}/templates/${id}`),
    create: (data) => fetchJSON(`${API_BASE}/templates`, { method: "POST", body: JSON.stringify(data) }),
    update: (id, data) => fetchJSON(`${API_BASE}/templates/${id}`, { method: "PUT", body: JSON.stringify(data) }),
    delete: (id) => fetch(`${API_BASE}/templates/${id}`, { method: "DELETE" }),
  },

  export: {
    json: (id) => `${API_BASE}/datasets/${id}/export/json`,
    csv: (id) => `${API_BASE}/datasets/${id}/export/csv`,
    sql: (id) => `${API_BASE}/datasets/${id}/export/sql`,
  },
};