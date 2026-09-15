// Thin fetch wrapper shared by every page. No demo/fake data lives here —
// every call hits the real FastAPI backend.
const API_BASE = "/api/v1";

function getToken() {
  return localStorage.getItem("omnisure_token");
}

function setSession(token, user) {
  localStorage.setItem("omnisure_token", token);
  localStorage.setItem("omnisure_user", JSON.stringify(user));
}

function clearSession() {
  localStorage.removeItem("omnisure_token");
  localStorage.removeItem("omnisure_user");
}

function getUser() {
  const raw = localStorage.getItem("omnisure_user");
  return raw ? JSON.parse(raw) : null;
}

function requireAuth() {
  if (!getToken()) {
    window.location.href = "/login.html";
  }
}

async function apiFetch(path, options = {}) {
  const headers = options.headers || {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (options.body && !(options.body instanceof URLSearchParams)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    clearSession();
    window.location.href = "/login.html";
    return null;
  }

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const message = (data && data.detail) || `Request failed (${res.status})`;
    throw new Error(message);
  }
  return data;
}

function formatINR(amount) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(
    amount || 0
  );
}
