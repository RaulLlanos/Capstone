import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function RoleRoute({ roles = [], children }) {
  const { user } = useAuth(); // { name, role, email } ó null

  if (!user) return <Navigate to="/login" replace />;

  const role = (user.role || "").toLowerCase();
  if (!roles.includes(role)) return <Navigate to="/" replace />;

  return children;
}
