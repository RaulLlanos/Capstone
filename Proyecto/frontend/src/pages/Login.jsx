import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../services/api";           // <— usamos axios con cookies
import styles from "./Login.module.css";

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!email || !password) {
      setError("Completa email y password.");
      return;
    }

    try {
      setLoading(true);

      // 1) Asegurar cookie CSRF (la API devuelve csrftoken)
      await api.get("/auth/csrf");

      // 2) Login (setea cookies HttpOnly: access/refresh)
      await api.post("/auth/login", { email, password });

      // 3) Traer los datos del usuario autenticado (incluye rol)
      const { data: me } = await api.get("/auth/me");
      // Espera algo como: { id, email, first_name, last_name, role|rol }

      const role = (me.role || me.rol || "tecnico").toLowerCase();
      const name =
        (me.first_name || "") + (me.last_name ? ` ${me.last_name}` : "");

      // 4) Guardar sesión en tu AuthContext
      // Como el token es cookie HttpOnly, guardamos un marcador local
      login({ token: "cookie", user: { name: name.trim() || email, role, email: me.email } });

      // 5) Redirigir según rol
      navigate(role === "auditor" ? "/auditor" : "/tecnico", { replace: true });
    } catch (err) {
      console.error(err);
      setError("Credenciales inválidas o error del servidor.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.wrapper}>
      <div className={styles.card}>
        <header className={styles.header}>
          <h1 className={styles.title}>Ingresar</h1>
          <p className={styles.subtitle}>Portal de gestión de técnicos</p>
        </header>

        <form onSubmit={handleSubmit} className={styles.form}>
          <label className={styles.label}>
            Email
            <input
              className={styles.input}
              type="email"
              placeholder="nombre@correo.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="username"
              disabled={loading}
            />
          </label>

          <label className={styles.label}>
            Password
            <input
              className={styles.input}
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              disabled={loading}
            />
          </label>

          {error && <div className={styles.error}>{error}</div>}

          <div className={styles.actions}>
            <button type="submit" className={styles.button} disabled={loading}>
              {loading ? "Ingresando..." : "Entrar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
