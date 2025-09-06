import { useState } from "react";
import { useNavigate } from "react-router-dom";
//import api from "../services/api"; // más adelante conectaremos al backend
import styles from "./Login.module.css"; // podemos reutilizar estilos del login

export default function Registro() {
  const navigate = useNavigate();

  const [nombre, setNombre] = useState("");
  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");
  const [rol, setRol] = useState("tecnico");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!nombre || !correo || !password) {
      setError("Completa todos los campos.");
      return;
    }

    try {
      setLoading(true);
      // Mock: por ahora simulamos éxito
      console.log("Registro enviado:", { nombre, correo, password, rol });

      // más adelante → await api.post("/usuarios/", { ... })

      alert("Usuario registrado correctamente (mock).");
      navigate("/login");
    } catch (err) {
      console.error(err);
      setError("Error al registrar usuario.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.wrapper}>
      <div className={styles.card}>
        <header className={styles.header}>
          <h1 className={styles.title}>Registro</h1>
          <p className={styles.subtitle}>Crea una cuenta nueva</p>
        </header>

        <form onSubmit={handleSubmit} className={styles.form}>
          <label className={styles.label}>
            Nombre completo
            <input
              className={styles.input}
              type="text"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              disabled={loading}
            />
          </label>

          <label className={styles.label}>
            Correo
            <input
              className={styles.input}
              type="email"
              value={correo}
              onChange={(e) => setCorreo(e.target.value)}
              disabled={loading}
            />
          </label>

          <label className={styles.label}>
            Contraseña
            <input
              className={styles.input}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
            />
          </label>

          <label className={styles.label}>
            Rol
            <select
              className={styles.select}
              value={rol}
              onChange={(e) => setRol(e.target.value)}
              disabled={loading}
            >
              <option value="tecnico">Técnico</option>
              <option value="auditor">Auditor</option>
              <option value="admin">Administrador</option>
            </select>
          </label>

          {error && <div className={styles.error}>{error}</div>}

          <div className={styles.actions}>
            <button type="submit" className={styles.button} disabled={loading}>
              {loading ? "Registrando..." : "Registrarse"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
