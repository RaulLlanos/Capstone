// src/routes/AppRouter.jsx
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  Outlet,
  useLocation,
  useNavigate,
  useParams,
} from "react-router-dom";
import { useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import NavBar from "../components/NavBar";

import AuditorDashboard from "../pages/Auditor";
import TecnicoDashboard from "../pages/Tecnico";
import Registro from "../pages/Registro";
import Login from "../pages/Login";
import AuditorDireccionAdd from "../pages/AuditorDireccionAdd";
import AuditorHistorial from "../pages/AuditorHistorial";
import TecnicoDireccionesLista from "../pages/TecnicoDireccionesLista";
import AuditorDireccionesLista from "../pages/AuditorDireccionesLista";
import AuditorDireccionEdit from "../pages/AuditorDireccionEdit";
import TecnicoReagendar from "../pages/TecnicoReagendar";
import TecnicoAuditoriaAdd from "../pages/TecnicoAuditoriaAdd";
import TecnicoAuditoriaVer from "../pages/TecnicoAuditoriaVer";
import TecnicoCompletadas from "../pages/TecnicoCompletadas";
import AdminUsuariosLista from "../pages/AdminUsuariosLista";
import AdminUsuarioEdit from "../pages/AdminUsuarioEdit";
import AdminAuditoriasLista from "../pages/AdminAuditoriasLista";

/** Puente que copia params y arma la URL destino (evita ":id" literal) */
function RedirectWithParams({ toPattern }) {
  const params = useParams();
  let to = toPattern;
  Object.entries(params).forEach(([k, v]) => {
    to = to.replace(`:${k}`, encodeURIComponent(v));
  });
  return <Navigate to={to} replace />;
}

/** Guard 1: autenticación */
function RequireAuth() {
  const { user, initializing } = useAuth();
  if (initializing) return null;
  if (!user) return <Navigate to="/login" replace />;
  return <Outlet />;
}

/** Guard 2: rol específico (usa rol normalizado) */
function RequireRole({ allowed }) {
  const { user, initializing } = useAuth();
  if (initializing) return null;
  if (!user) return <Navigate to="/login" replace />;
  const role = String(user?.role || user?.rol || "").toLowerCase();
  return allowed.includes(role) ? <Outlet /> : <Forbidden />;
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
  const role = String(user?.role || user?.rol || "").toLowerCase();
  return role === "administrador"
    ? <Navigate to="/auditor" replace />
    : <Navigate to="/tecnico" replace />;
}

/** Layout con lastRoute */
function AppShell() {
  const { user, logout, initializing } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    if (location.pathname !== "/login") {
      try { localStorage.setItem("lastRoute", location.pathname + location.search); } catch {}
    }
  }, [location.pathname, location.search]);

  useEffect(() => {
    if (!initializing && user && location.pathname === "/login") {
      const last = localStorage.getItem("lastRoute") || "/";
      navigate(last, { replace: true });
    }
  }, [initializing, user, location.pathname, navigate]);

  return (
    <>
      {!initializing && user && <NavBar user={user} onLogout={logout} />}

      <Routes>
        {/* Público */}
        <Route path="/login" element={<Login />} />

        {/* Autenticado */}
        <Route element={<RequireAuth />}>
          <Route index element={<RedirectByRole />} />

          {/* ADMIN (rol "administrador") */}
          <Route element={<RequireRole allowed={["administrador"]} />}>
            <Route path="/auditor" element={<AuditorDashboard />} />
            <Route path="/registro" element={<Registro />} />

            {/* Panel (antes /admin/..., ahora /panel/...) */}
            <Route path="/panel/usuarios" element={<AdminUsuariosLista />} />
            <Route path="/panel/usuarios/:id/editar" element={<AdminUsuarioEdit />} />
            <Route path="/panel/auditorias" element={<AdminAuditoriasLista />} />
            <Route path="/panel/auditorias/:id" element={<TecnicoAuditoriaVer />} />

            {/* Auditor: direcciones */}
            <Route path="/auditor/direcciones/nueva" element={<AuditorDireccionAdd />} />
            <Route path="/auditor/direcciones" element={<AuditorDireccionesLista />} />
            <Route path="/auditor/direcciones/:id/editar" element={<AuditorDireccionEdit />} />
            <Route path="/auditor/historial" element={<AuditorHistorial />} />

            {/* Redirecciones legadas /admin/... -> /panel/... (con params reales) */}
            <Route path="/admin/usuarios" element={<Navigate to="/panel/usuarios" replace />} />
            <Route
              path="/admin/usuarios/:id/editar"
              element={<RedirectWithParams toPattern="/panel/usuarios/:id/editar" />}
            />
            <Route path="/admin/auditorias" element={<Navigate to="/panel/auditorias" replace />} />
            <Route
              path="/admin/auditorias/:id"
              element={<RedirectWithParams toPattern="/panel/auditorias/:id" />}
            />
          </Route>

          {/* TECNICO */}
          <Route element={<RequireRole allowed={["tecnico"]} />}>
            <Route path="/tecnico" element={<TecnicoDashboard />} />
            <Route path="/tecnico/direcciones" element={<TecnicoDireccionesLista />} />
            <Route path="/tecnico/reagendar/:id" element={<TecnicoReagendar />} />
            <Route path="/tecnico/auditoria/nueva/:id" element={<TecnicoAuditoriaAdd />} />
            <Route path="/tecnico/auditoria/ver/:id" element={<TecnicoAuditoriaVer />} />
            <Route path="/tecnico/completadas" element={<TecnicoCompletadas />} />
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
