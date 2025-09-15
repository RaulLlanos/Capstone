// AppRouter.jsx
import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext"; // ya existente
import NavBar from "../components/NavBar";     // tu NavBar existente con NavBar.module.css
import AuditorDashboard from "../pages/Auditor";
import TecnicoDashboard from "../pages/Tecnico";
import Registro from "../pages/Registro";
import Login from "../pages/Login";

function RequireAuth() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return <Outlet />;
}

function RequireRole({ allowed /* array de strings lowercase */ }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return allowed.includes(user.role) ? <Outlet /> : <Forbidden />;
}

function Forbidden() {
  return (
    <div style={{ padding: 24 }}>
      <h2>403 - No autorizado</h2>
      <p>No tienes permiso para acceder a esta página.</p>
    </div>
  );
}

function RedirectByRole() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return user.role === "auditor"
    ? <Navigate to="/auditor" replace />
    : <Navigate to="/tecnico" replace />;
}

export default function AppRouter() {
  const { user, logout } = useAuth();

  return (
    <BrowserRouter>
      {/* Mostrar tu NavBar solo si hay sesión */}
      {user && (
        <NavBar
          // props opcionales por si tu NavBar las usa
          user={user}
          onLogout={logout}
        />
      )}

      <Routes>
        {/* Público */}
        <Route path="/login" element={<Login />} />

        {/* Autenticado */}
        <Route element={<RequireAuth />}>
          <Route index element={<RedirectByRole />} />

          {/* AUDITOR */}
          <Route element={<RequireRole allowed={["auditor"]} />}>
            <Route path="/auditor" element={<AuditorDashboard />} />
            <Route path="/registro" element={<Registro />} /> {/* <- solo auditor */}
          </Route>

          {/* TECNICO */}
          <Route element={<RequireRole allowed={["tecnico"]} />}>
            <Route path="/tecnico" element={<TecnicoDashboard />} />
          </Route>
        </Route>

        {/* 404 */}
        <Route path="*" element={<div style={{ padding: 24 }}><h2>404</h2></div>} />
      </Routes>
    </BrowserRouter>
  );
}
