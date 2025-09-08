// src/components/PublicLayout.jsx
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import logo from "../assets/logo.png";

export default function PublicLayout({ children }) {
  const { user } = useAuth();

  const role = user ? String(user.role).toLowerCase() : "";
  const home = role === "auditor" ? "/auditor" : role === "tecnico" ? "/tecnico" : "/login";

  return (
    <div>
      <header
        style={{
          display: "flex",
          alignItems: "center",
          padding: "10px 16px",
          borderBottom: "1px solid #eee",
          background: "#fff",
        }}
      >
        <Link to={home}>
          <img src={logo} alt="logo" style={{ height: 32 }} />
        </Link>
      </header>
      <main>{children}</main>
    </div>
  );
}
