// src/services/api.js
import axios from "axios";

// lee cookie por nombre (para CSRF si lo necesitas en algún punto)
function getCookie(name) {
  const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return m ? decodeURIComponent(m.pop()) : "";
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  withCredentials: true, // ¡clave para cookies HttpOnly!
});

// interceptor opcional por si necesitas enviar X-CSRFToken en algún POST/PATCH
api.interceptors.request.use((config) => {
  const method = (config.method || "get").toLowerCase();
  if (["post", "put", "patch", "delete"].includes(method)) {
    const token = getCookie("csrftoken");
    if (token) config.headers["X-CSRFToken"] = token;
  }
  return config;
});

export default api;
