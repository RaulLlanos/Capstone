import { BrowserRouter, Routes, Route, Navigate, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import NavBar from "../components/NavBar";

import AuditorDashboard from "../pages/Auditor";
import TecnicoDashboard from "../pages/Tecnico";
import Registro from "../pages/Registro";
import Login from "../pages/Login";
import AuditorDireccionAdd from "../pages/AuditorDireccionAdd";
import TecnicoDireccionesLista from "../pages/TecnicoDireccionesLista";
import AuditorDireccionesLista from "../pages/AuditorDireccionesLista";
import AuditorDireccionEdit from "../pages/AuditorDireccionEdit";
import TecnicoReagendar from "../pages/TecnicoReagendar"
import TecnicoAuditoriaAdd from "../pages/TecnicoAuditoriaAdd";
import TecnicoAuditoriaVer from "../pages/TecnicoAuditoriaVer";

/** Guard 1: autenticación básica */
function RequireAuth() {
  const { user, initializing } = useAuth();

  // Mientras verificamos sesión (F5), no decidas aún
  if (initializing) return null; // o un spinner si quieres

  if (!user) return <Navigate to="/login" replace />;
  return <Outlet />;
}

/** Guard 2: rol específico (lowercase) */
function RequireRole({ allowed /* array de strings lowercase */ }) {
  const { user, initializing } = useAuth();

  if (initializing) return null;

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
  const { user, initializing } = useAuth();

  if (initializing) return null;
  if (!user) return <Navigate to="/login" replace />;

  return user.role === "administrador"
    ? <Navigate to="/auditor" replace />
    : <Navigate to="/tecnico" replace />;
}

/** Layout con efectos de lastRoute */
function AppShell() {
  const { user, logout, initializing } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  // Guarda la última ruta (excepto /login)
  useEffect(() => {
    if (location.pathname !== "/login") {
      try {
        localStorage.setItem("lastRoute", location.pathname + location.search);
      } catch { /* empty */ }
    }
  }, [location.pathname, location.search]);

  // Si ya estamos logueados y (por refresh) quedamos en /login,
  // al terminar de inicializar vuelve a la última ruta guardada.
  useEffect(() => {
    if (!initializing && user && location.pathname === "/login") {
      const last = localStorage.getItem("lastRoute") || "/";
      navigate(last, { replace: true });
    }
  }, [initializing, user, location.pathname, navigate]);

  return (
    <>
      {/* Muestra NavBar solo cuando ya terminó la inicialización y hay sesión */}
      {!initializing && user && <NavBar user={user} onLogout={logout} />}

      <Routes>
        {/* Público */}
        <Route path="/login" element={<Login />} />

        {/* Autenticado */}
        <Route element={<RequireAuth />}>
          <Route index element={<RedirectByRole />} />

          {/* AUDITOR */}
          <Route element={<RequireRole allowed={["administrador"]} />}>
            <Route path="/auditor" element={<AuditorDashboard />} />
            <Route path="/registro" element={<Registro />} />
            <Route path="/auditor/direcciones/nueva" element={<AuditorDireccionAdd />} />
            <Route path="/auditor/direcciones" element={<AuditorDireccionesLista />} />
            <Route path="/auditor/direcciones/:id/editar" element={<AuditorDireccionEdit />} />
          </Route>

          {/* TECNICO */}
          <Route element={<RequireRole allowed={["tecnico"]} />}>
            <Route path="/tecnico" element={<TecnicoDashboard />} />
            <Route path="/tecnico/direcciones" element={<TecnicoDireccionesLista />} />
            <Route path="/tecnico/reagendar/:id" element={<TecnicoReagendar />} />
            <Route path="/tecnico/auditoria/nueva/:id" element={<TecnicoAuditoriaAdd />} />
            <Route path="/tecnico/auditoria/ver/:id" element={<TecnicoAuditoriaVer />} />
          </Route>
        </Route>

        {/* 404 */}
        <Route path="*" element={<div style={{ padding: 24 }}><h2>404</h2></div>} />
      </Routes>
    </>
  );
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  );
}
