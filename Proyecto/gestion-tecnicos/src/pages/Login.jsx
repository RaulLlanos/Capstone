import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

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
    const fakeToken = "dev-token";
    const fakeUser = { name: email, role };
    login({ token: fakeToken, user: fakeUser });
    navigate(role === "auditor" ? "/auditor" : "/tecnico", { replace: true });
  };

  return (
    <div style={{ maxWidth: 360, margin: "48px auto" }}>
      <h2>Iniciar Sesión</h2>
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: 12 }}>
        <label>
          Email
          <input
            type="email"
            placeholder="nombre@correo.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        <label>
          Password
          <input
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        <label>
          Rol
          <select value={role} onChange={(e) => setRole(e.target.value)}>
            <option value="tecnico">Técnico</option>
            <option value="auditor">Auditor</option>
          </select>
        </label>
        {error && <div style={{ color: "crimson" }}>{error}</div>}
        <button type="submit">Entrar</button>
      </form>
    </div>
  );
}
