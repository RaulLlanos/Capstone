// src/components/NavBar.jsx
import { useState, useMemo } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import styles from "./NavBar.module.css";

export default function NavBar() {
  // 🔒 TODOS los hooks al inicio SIEMPRE
  const { user, logout } = useAuth() || {};
  const location = useLocation();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  // flag para ocultar en /login (no hagas return antes de los hooks)
  const hide = location?.pathname === "/login";

  const handleLogout = () => {
    try { localStorage.removeItem("lastRoute"); } catch { /* empty */ }
    if (typeof logout === "function") logout();
    navigate("/login", { replace: true });
  };

  const displayName = (user?.name || user?.email || "Usuario").trim();
  const initial = (displayName[0] || "?").toUpperCase();
  const role = String(user?.role || user?.rol || "").toLowerCase();
  const isAdmin = role === "administrador";
  const isTecnico = role === "tecnico";
  const roleLabel = isAdmin ? "Administrador" : isTecnico ? "Técnico" : "Usuario";

  const links = useMemo(() => {
    if (!user) return [];
    if (isAdmin) {
      return [
        { to: "/auditor/direcciones", label: "Direcciones" },
        { to: "/admin/usuarios", label: "Usuarios" },
        { to: "/admin/auditorias", label: "Auditorias" },
        { to: "/auditor/historial", label: "Historial" }
      ];
    }
    if (isTecnico) return [
      { to: "/tecnico/direcciones", label: "Direcciones" },
      { to: "/tecnico/completadas", label: "Visitadas" }
    ];
    return [];
  }, [user, isAdmin, isTecnico]);

  // Si hay que ocultar, renderiza nada (pero los hooks ya se llamaron todos)
  if (hide) return null;

  return (
    <header className={styles.wrapper}>
      <div className={styles.inner}>
        {/* Brand con SVG inline (evita rutas rotas) */}
        <Link to="/" className={styles.brand} aria-label="Inicio">
          <span className={styles.brandText}>Gestión Técnicos</span>
        </Link>

        {/* Desktop nav */}
        <nav className={styles.navDesktop} aria-label="Principal">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              className={({ isActive }) =>
                [styles.navLink, isActive ? styles.navLinkActive : ""].join(" ")
              }
              end
            >
              {l.label}
            </NavLink>
          ))}
        </nav>

        {/* Right */}
        {user && (
          <div className={styles.right}>
            <div className={styles.userBadge} title={displayName}>
              <div className={styles.avatar}>{initial}</div>
              <div className={styles.userInfo}>
                <div className={styles.userName}>{displayName}</div>
                <div className={`${styles.role} ${isAdmin ? styles.roleAuditor : styles.roleTecnico}`}>
                  {roleLabel}
                </div>
              </div>
            </div>

            <button className={styles.logoutBtn} onClick={handleLogout}>
              Cerrar sesión
            </button>

            {/* Burger (mobile) */}
            <button
              className={styles.burger}
              aria-label="Abrir menú"
              aria-expanded={open}
              onClick={() => setOpen((o) => !o)}
            >
              <span />
              <span />
              <span />
            </button>
          </div>
        )}
      </div>

      {/* Mobile menu */}
      {user && (
        <div className={[styles.navMobile, open ? styles.navMobileOpen : ""].join(" ")}>
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              className={({ isActive }) =>
                [styles.mobileLink, isActive ? styles.mobileLinkActive : ""].join(" ")
              }
              onClick={() => setOpen(false)}
              end
            >
              {l.label}
            </NavLink>
          ))}
          <button
            className={styles.mobileLogout}
            onClick={() => { setOpen(false); handleLogout(); }}
          >
            Cerrar sesión
          </button>
        </div>
      )}
    </header>
  );
}
