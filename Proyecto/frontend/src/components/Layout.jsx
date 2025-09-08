// src/components/Layout.jsx
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import logo from "../assets/logo.png";

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  // home según rol
  const role = user ? String(user.role).toLowerCase() : "";
  const home = role === "auditor" ? "/auditor" : "/tecnico";

  return (
    <div className="app-shell">
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "10px 16px",
          borderBottom: "1px solid #eee",
          background: "#fff",
        }}
      >
        <nav style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <Link to={home}>
            <img src={logo} alt="logo" style={{ height: 32 }} />
          </Link>
        </nav>

        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
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
