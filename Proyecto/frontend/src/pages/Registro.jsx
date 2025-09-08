// src/pages/Registro.jsx
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
//import api from "../services/api";            // lo usaremos cuando haya backend
import styles from "./Login.module.css";      // reutilizamos estilos del login

const emailRegex =
  /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/i; // formato de email razonable

export default function Registro() {
  const navigate = useNavigate();

  const [nombre, setNombre] = useState("");
  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");
  const [rol, setRol] = useState("tecnico");

  const [touched, setTouched] = useState({ nombre: false, correo: false, password: false });
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");

  // Validaciones
  const errors = useMemo(() => {
    const e = {};
    if (!nombre.trim()) e.nombre = "Ingresa tu nombre.";
    if (!correo.trim()) e.correo = "Ingresa tu correo.";
    else if (!emailRegex.test(correo.trim())) e.correo = "Formato de correo inválido.";
    if (!password) e.password = "Ingresa una contraseña.";
    else if (password.length < 8) e.password = "La contraseña debe tener al menos 8 caracteres.";
    return e;
  }, [nombre, correo, password]);

  const isValid = Object.keys(errors).length === 0;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitError("");
    setTouched({ nombre: true, correo: true, password: true });

    if (!isValid) return;

    try {
      setSubmitting(true);

      // MOCK: por ahora no llamamos backend; solo simulamos éxito
      // Cuando haya endpoint:
      // await api.post("/usuarios/", { nombre, email: correo, password, rol });

      alert("Usuario registrado correctamente (mock).");
      navigate("/login");
    } catch (err) {
      console.error(err);
      setSubmitError("Error al registrar usuario. Intenta nuevamente.");
    } finally {
      setSubmitting(false);
    }
  };

  // Accesibilidad: limpiar error de submit al modificar campos
  useEffect(() => {
    if (submitError) setSubmitError("");
  }, [nombre, correo, password, rol]); // eslint-disable-line

  return (
    <div className={styles.wrapper}>
      <div className={styles.card}>
        <header className={styles.header}>
          <h1 className={styles.title}>Registro</h1>
          <p className={styles.subtitle}>Crea una cuenta nueva</p>
        </header>

        <form onSubmit={handleSubmit} className={styles.form} noValidate>
          {/* Nombre */}
          <label className={styles.label}>
            Nombre completo
            <input
              className={styles.input}
              type="text"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              onBlur={() => setTouched((t) => ({ ...t, nombre: true }))}
              disabled={submitting}
              aria-invalid={!!errors.nombre}
              aria-describedby="err-nombre"
            />
          </label>
          {touched.nombre && errors.nombre && (
            <div id="err-nombre" className={styles.error}>{errors.nombre}</div>
          )}

          {/* Correo */}
          <label className={styles.label}>
            Correo
            <input
              className={styles.input}
              type="email"
              value={correo}
              onChange={(e) => setCorreo(e.target.value)}
              onBlur={() => setTouched((t) => ({ ...t, correo: true }))}
              disabled={submitting}
              autoComplete="username"
              aria-invalid={!!errors.correo}
              aria-describedby="err-correo"
            />
          </label>
          {touched.correo && errors.correo && (
            <div id="err-correo" className={styles.error}>{errors.correo}</div>
          )}

          {/* Password */}
          <label className={styles.label}>
            Contraseña
            <input
              className={styles.input}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onBlur={() => setTouched((t) => ({ ...t, password: true }))}
              disabled={submitting}
              autoComplete="new-password"
              aria-invalid={!!errors.password}
              aria-describedby="err-password"
            />
          </label>
          {touched.password && errors.password && (
            <div id="err-password" className={styles.error}>{errors.password}</div>
          )}
          <div style={{ fontSize: 12, color: "#6b7280", marginTop: -6 }}>
            Mínimo 8 caracteres.
          </div>

          {/* Rol */}
          <label className={styles.label}>
            Rol
            <select
              className={styles.select}
              value={rol}
              onChange={(e) => setRol(e.target.value)}
              disabled={submitting}
            >
              <option value="tecnico">Técnico</option>
              <option value="auditor">Auditor</option>
              <option value="admin">Administrador</option>
            </select>
          </label>

          {submitError && <div className={styles.error}>{submitError}</div>}

          <div className={styles.actions}>
            <button
              type="submit"
              className={styles.button}
              disabled={submitting || !isValid}
              title={!isValid ? "Completa los campos requeridos" : "Registrarse"}
            >
              {submitting ? "Registrando..." : "Registrarse"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
