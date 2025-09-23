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
    localStorage.removeItem("lastRoute");
    logout();
    navigate("/login", { replace: true });
  };

  // Inicial del usuario (si no viene name, usa email)
  const displayName = user?.name || user?.email || "Usuario";
  const initial = (displayName[0] || "?").toUpperCase();

  // Roles (tu backend usa lowercase)
  const isAuditor = user?.role === "auditor";
  const isTecnico = user?.role === "tecnico";
  const roleLabel = isAuditor ? "Auditor" : "Técnico";

  return (
    <header className={styles.header}>
      <div className={styles.left}>
        <Link to="/" className={styles.brand}>
          <img src="assets/logo.png" alt="logo" /> 
          <span className={styles.logoDot} />
          <span className={styles.brandText}>Gestión Técnicos</span>
        </Link>
      </div>

      <div className={styles.right}>
        {user && (
          <>
            {/* Acciones según rol */}
            {isAuditor && (
              <>
                <Link to="/registro" className={styles.logoutBtn}>
                  + Crear usuario
                </Link>
                <Link to="/auditor/direcciones/nueva" className={styles.logoutBtn}>
                  + Añadir dirección
                </Link>
              </>
            )}

            {isTecnico && (
              <Link to="/tecnico/direcciones" className={styles.logoutBtn}>
                Direcciones
              </Link>
            )}

            {/* Badge de usuario */}
            <div className={styles.userBadge} title={displayName}>
              <div className={styles.avatar}>{initial}</div>
              <div className={styles.userInfo}>
                <div className={styles.userName}>{displayName}</div>
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
