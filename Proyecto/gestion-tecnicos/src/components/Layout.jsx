// src/components/Layout.jsx
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="app-shell">
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "10px 16px",
          borderBottom: "1px solid #ffffffff",
        }}
      >
        <nav style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <strong>Gestión Técnicos</strong>
          <Link to="/tecnico">Técnico</Link>
          <Link to="/auditor">Auditor</Link>
        </nav>

        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <span style={{ fontSize: 14, color: "#666" }}>
            {user ? `${user.name} (${user.role})` : ""}
          </span>
          <button onClick={handleLogout}>Salir</button>
        </div>
      </header>

      <main style={{ padding: 16 }}>{children}</main>
    </div>
  );
}
