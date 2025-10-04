/* eslint-disable no-unused-vars */
// src/pages/TecnicoAuditoriaVer.jsx
import { useEffect, useState } from "react";
import { useNavigate, useParams, useLocation } from "react-router-dom";
import api from "../services/api";
import styles from "./Login.module.css";

const AUDIT_LIST_ENDPOINTS = [
  "/api/auditorias/",
  "/api/auditoria/instalacion/",
];

async function findAuditByAsignacion(asignacionId) {
  for (const ep of AUDIT_LIST_ENDPOINTS) {
    try {
      const res = await api.get(ep, { params: { asignacion: asignacionId } });
      const data = res.data;
      const list = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : [];
      if (list.length) return list[0];
    } catch { /* empty */ }
  }
  return null;
}

export default function TecnicoAuditoriaVer() {
  const { id } = useParams(); // id de asignación
  const navigate = useNavigate();
  const location = useLocation();

  const [audit, setAudit] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setLoading(true);
      const a = await findAuditByAsignacion(id);
      if (!a) {
        navigate("/tecnico", {
          replace: true,
          state: { flash: "No existe auditoría para esta dirección." },
        });
        return;
      }
      setAudit(a);
      setLoading(false);
    })();
  }, [id, navigate]);

  return (
    <div className={styles.wrapper}>
      <div className={styles.card} style={{ maxWidth: 720 }}>
        <header className={styles.header}>
          <h1 className={styles.title}>Auditoría registrada</h1>
          <p className={styles.subtitle}>Vista de solo lectura</p>
        </header>

        {loading ? (
          <div className={styles.helper}>Cargando…</div>
        ) : (
          <>
            <div className={styles.form} style={{ gap: 10 }}>
              <div className={styles.label}>
                <span className={styles.helper}>Asignación</span>
                <div className={styles.helper}><strong>{audit?.asignacion}</strong></div>
              </div>
              <div className={styles.label}>
                <span className={styles.helper}>Nombre auditor</span>
                <div className={styles.helper}>{audit?.nombre_auditor || "—"}</div>
              </div>
              <div className={styles.label}>
                <span className={styles.helper}>Estado cliente</span>
                <div className={styles.helper}>{audit?.estado_cliente || "—"}</div>
              </div>
            </div>

            {/* Evidencias */}
            <div style={{ marginTop: 12, display: "grid", gap: 10 }}>
              <div className={styles.helper} style={{ fontWeight: 700 }}>Evidencias</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
                {["foto1", "foto2", "foto3"].map((k) => (
                  <div key={k} style={{ border: "1px solid #e5e7eb", borderRadius: 8, padding: 8, minHeight: 120, display: "grid", placeItems: "center" }}>
                    {audit?.[k] ? (
                      <img src={audit[k]} alt={k} style={{ maxWidth: "100%", maxHeight: 200, objectFit: "contain" }} />
                    ) : (
                      <span className={styles.helper}>Sin {k}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className={styles.actions} style={{ marginTop: 12 }}>
              <button className={styles.button} onClick={() => navigate("/tecnico")}>
                Volver
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
