import axios from "axios";

// instancia con la baseURL que pusimos en .env.local
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
});

// interceptor que añade el token a cada request si existe
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// interceptor de respuesta (opcional ahora)
// si el backend devuelve 401 (no autorizado), limpiamos el token
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem("token");
    }
    return Promise.reject(error);
  }
);

export default api;
