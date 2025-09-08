import {
  createBrowserRouter,
  RouterProvider,
  Navigate,
  Outlet,
} from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Login from "../pages/Login";
import Tecnico from "../pages/Tecnico";
import Auditor from "../pages/Auditor";
import Registro from "../pages/Registro";
import Layout from "../components/Layout";
import PublicLayout from "../components/PublicLayout";

function PrivateRoute() {
  const { user, loading } = useAuth();
  if (loading) return <div style={{ padding: 24 }}>Cargando...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <Outlet />;
}

const router = createBrowserRouter([
  { path: "/login", 
    element:
    <PublicLayout> 
      <Login /> 
    </PublicLayout>
  },
  { path: "/registro", 
    element: 
    <PublicLayout>
      <Registro /> 
    </PublicLayout>
  },
  {
    element: <PrivateRoute />,
    children: [
      {
        path: "/tecnico",
        element: (
          <Layout>
            <Tecnico />
          </Layout>
        ),
      },
      {
        path: "/auditor",
        element: (
          <Layout>
            <Auditor />
          </Layout>
        ),
      },
    ],
  },
  { path: "*", element: <Navigate to="/login" replace /> },
]);

export default function AppRouter() {
  return <RouterProvider router={router} />;
}
