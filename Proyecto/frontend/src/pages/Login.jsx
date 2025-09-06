import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import styles from "./Login.module.css";

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("tecnico");
  const [error, setError] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    setError("");
    if (!email || !password) {
      setError("Completa email y password.");
      return;
    }
    // MOCK: reemplazar cuando tengas backend
    login({ token: "dev-token", user: { name: email, role } });
    navigate(role === "auditor" ? "/auditor" : "/tecnico", { replace: true });
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
            />
          </label>

          {/* Solo para el mock: selector de rol */}
          <label className={styles.label}>
            Rol
            <select
              className={styles.select}
              value={role}
              onChange={(e) => setRole(e.target.value)}
            >
              <option value="tecnico">Técnico</option>
              <option value="auditor">Auditor</option>
            </select>
          </label>

          {error && <div className={styles.error}>{error}</div>}

          <div className={styles.actions}>
            <button type="submit" className={styles.button}>
              Entrar
            </button>
            <div className={styles.helper}>
              <span>¿No tienes cuenta?</span>
              <a className={styles.link} href="/registro">
                Registrarse
              </a>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
