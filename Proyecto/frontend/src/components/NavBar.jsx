// src/components/NavBar.jsx
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import styles from "./NavBar.module.css";

export default function NavBar() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  // Ocultar en /login
  if (location.pathname === "/login") return null;

  const handleLogout = () => {
    // opcional: limpiar última ruta guardada
    localStorage.removeItem("lastRoute");
    logout();
    navigate("/login", { replace: true });
  };

  const initial = user?.name?.[0]?.toUpperCase() || "?";
  const isAuditor = user?.role === "auditor";
  const roleLabel = isAuditor ? "Auditor" : "Técnico";

  return (
    <header className={styles.header}>
      <div className={styles.left}>
        <Link to="/" className={styles.brand}>
          {/* tu logo si quieres <img src="/logo.svg" alt="logo" /> */}
          <span className={styles.logoDot} />
          <span className={styles.brandText}>Gestión Técnicos</span>
        </Link>
      </div>

      <div className={styles.right}>
        {user && (
          <>
            {/* Botón visible solo para AUDITOR */}
            {isAuditor && (
              <Link
                to="/registro"
                // Si tienes otra clase para botón principal, reemplaza logoutBtn por esa (ej: styles.primaryBtn)
                className={styles.logoutBtn}
              >
                + Crear usuario
              </Link>
            )}

            <div className={styles.userBadge} title={user.name || ""}>
              <div className={styles.avatar}>{initial}</div>
              <div className={styles.userInfo}>
                <div className={styles.userName}>{user.name || "Usuario"}</div>
                <div
                  className={`${styles.role} ${
                    isAuditor ? styles.roleAuditor : styles.roleTecnico
                  }`}
                >
                  {roleLabel}
                </div>
              </div>
            </div>

            <button className={styles.logoutBtn} onClick={handleLogout}>
              Cerrar sesión
            </button>
          </>
        )}
      </div>
    </header>
  );
}
