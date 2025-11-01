/* eslint-disable no-unused-vars */
// src/pages/AdminAuditoriasLista.jsx
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";
import styles from "./Login.module.css";

function asArray(x) {
  if (Array.isArray(x)) return x;
  if (x && Array.isArray(x.results)) return x.results;
  return [];
}

function safeStr(x, fallback = "—") {
  if (x === null || x === undefined) return fallback;
  const s = String(x).trim();
  return s ? s : fallback;
}

function ensureObj(v) {
  return v && typeof v === "object" ? v : null;
}

export default function AdminAuditoriasLista() {
  const { user } = useAuth();
  const role = String(user?.rol || user?.role || "").toLowerCase();
  const isAdmin = role === "administrador";

  const [rows, setRows] = useState([]);            // auditorías (con asignación hidratada)
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // filtros
  const [q, setQ] = useState("");
  const [fTec, setFTec] = useState("");
  const [fCom, setFCom] = useState("");
  const [fMar, setFMar] = useState("");

  // opciones dinámicas
  const [optTecnicos, setOptTecnicos] = useState([]); // {value, label}
  const [optComunas, setOptComunas] = useState([]);
  const [optMarcas, setOptMarcas] = useState([]);

  // ------ carga auditorías y “hidratación” de asignación ------
  useEffect(() => {
    (async () => {
      setLoading(true);
      setError("");
      try {
        // Trae auditorías (todas o paginadas). Si tu endpoint es paginado, iteramos next
        let url = "/api/auditorias/";
        let acc = [];
        for (;;) {
          const res = await api.get(url);
          const chunk = asArray(res.data);
          acc = acc.concat(chunk);
          const next = res.data?.next;
          if (!next) break;
          url = next; // DRF next absoluto
        }

        // Si asignacion viene como id, hidratar con GET /api/asignaciones/{id}/
        const needIds = Array.from(
          new Set(
            acc
              .map(a => (typeof a.asignacion === "number" ? a.asignacion : null))
              .filter(Boolean)
          )
        );
        // Hidratar en paralelo (simple y efectivo)
        const idToAsign = {};
        await Promise.all(
          needIds.map(async (id) => {
            try {
              const res = await api.get(`/api/asignaciones/${id}/`);
              idToAsign[id] = res.data || {};
            } catch {
              idToAsign[id] = { id, _error: true };
            }
          })
        );

        // Normaliza: a.asignacion siempre objeto
        const hydrated = acc.map((a) => {
          if (ensureObj(a.asignacion)) return a; // ya viene expandida
          if (typeof a.asignacion === "number") {
            return { ...a, asignacion: idToAsign[a.asignacion] || { id: a.asignacion } };
          }
          // nulo o desconocido
          return { ...a, asignacion: a.asignacion || {} };
        });

        setRows(hydrated);

        // construir opciones dinámicas
        const tecnicosSet = new Map(); // value=id|email, label
        const comunasSet = new Set();
        const marcasSet = new Set();

        hydrated.forEach((a) => {
          const asg = a.asignacion || {};
          const tecObj = ensureObj(asg.asignado_a) || ensureObj(asg.tecnico);
          const tecId =
            (tecObj && (tecObj.id ?? tecObj.pk)) ||
            (typeof asg.asignado_a === "number" ? asg.asignado_a : null) ||
            null;
        const tecName =
            (tecObj && (tecObj.name || tecObj.full_name || tecObj.display_name || tecObj.email)) ||
            asg.asignado_a_email ||
            (tecId ? `Tec #${tecId}` : "");
          if (tecId) tecnicosSet.set(String(tecId), tecName || `Tec #${tecId}`);
          if (asg.comuna) comunasSet.add(String(asg.comuna));
          if (asg.marca) marcasSet.add(String(asg.marca));
        });

        // Además, intenta traer técnicos “oficiales”
        try {
          const r = await api.get("/api/usuarios/?role=tecnico");
          const cand = asArray(r.data).map((u) => {
            const id = u.id ?? u.pk;
            const lbl =
              u.name ||
              (u.first_name || u.last_name ? `${u.first_name || ""} ${u.last_name || ""}`.trim() : "") ||
              u.full_name ||
              u.display_name ||
              u.email ||
              (id ? `Tec #${id}` : "Técnico");
            return { value: String(id), label: lbl };
          }).filter(x => x.value);
          cand.forEach(({ value, label }) => {
            if (!tecnicosSet.has(value)) tecnicosSet.set(value, label);
          });
        } catch (_) {
          // si falla, usamos solo los encontrados en datos
        }

        setOptTecnicos([{ value: "", label: "Todos los técnicos" }].concat(
          Array.from(tecnicosSet.entries()).map(([value, label]) => ({ value, label }))
        ));
        setOptComunas([{ value: "", label: "Todas las comunas" }].concat(
          Array.from(comunasSet.values()).sort().map(c => ({ value: c, label: c }))
        ));
        setOptMarcas([{ value: "", label: "Todas las marcas" }].concat(
          Array.from(marcasSet.values()).sort().map(m => ({ value: m, label: m }))
        ));
      } catch (err) {
        console.error(err);
        setError("No se pudieron cargar las auditorías.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  // ------ filtros ------
  const filtered = useMemo(() => {
    const txt = q.trim().toLowerCase();
    return rows.filter((a) => {
      const asg = a.asignacion || {};

      // técnico: acepta tanto id (value del select) como objeto
      if (fTec) {
        const tecObj = ensureObj(asg.asignado_a) || ensureObj(asg.tecnico);
        const tecId =
          (tecObj && (tecObj.id ?? tecObj.pk)) ||
          (typeof asg.asignado_a === "number" ? asg.asignado_a : null) ||
          null;
        if (String(tecId || "") !== String(fTec)) return false;
      }
      if (fCom && String(asg.comuna || "") !== fCom) return false;
      if (fMar && String(asg.marca || "") !== fMar) return false;

      if (!txt) return true;

      const bag = [
        asg.direccion,
        asg.comuna,
        asg.marca,
        asg.tecnologia,
        asg.id_vivienda,
        asg.rut_cliente,
        asg.fecha,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      return bag.includes(txt);
    });
  }, [rows, q, fTec, fCom, fMar]);

  if (!isAdmin) {
    return (
      <div className={styles.wrapper}>
        <div className={styles.card}>
          <p className={styles.error}>Solo los administradores pueden acceder a esta sección.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.card} style={{ maxWidth: 1100 }}>
        <header className={styles.header}>
          <h1 className={styles.title}>Auditorías completadas</h1>
          <p className={styles.subtitle}>Filtra y revisa las visitas realizadas</p>
        </header>

        {/* Filtros */}
        <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr 1fr 1fr", gap: 8 }}>
          <input
            className={styles.input}
            placeholder="Buscar dirección / id vivienda / rut…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <select className={styles.select} value={fTec} onChange={(e) => setFTec(e.target.value)}>
            {optTecnicos.map(o => <option key={o.value || "__all"} value={o.value}>{o.label}</option>)}
          </select>
          <select className={styles.select} value={fCom} onChange={(e) => setFCom(e.target.value)}>
            {optComunas.map(o => <option key={o.value || "__all"} value={o.value}>{o.label}</option>)}
          </select>
          <select className={styles.select} value={fMar} onChange={(e) => setFMar(e.target.value)}>
            {optMarcas.map(o => <option key={o.value || "__all"} value={o.value}>{o.label}</option>)}
          </select>
        </div>

        {error && <div className={styles.error} style={{ marginTop: 8 }}>{error}</div>}
        {loading && <div className={styles.helper} style={{ marginTop: 8 }}>Cargando…</div>}

        <div style={{ overflowX: "auto", marginTop: 12 }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={{whiteSpace:"nowrap"}}>ID</th>
                <th>Fecha</th>
                <th>Dirección</th>
                <th>Comuna</th>
                <th>Técnico</th>
                <th>Marca</th>
                <th style={{ width: 160 }}>Acción</th>
              </tr>
            </thead>
            <tbody>
            {filtered.map((a) => {
                const asg = a.asignacion || {};

                // técnico
                const tecObj =
                (asg.asignado_a && typeof asg.asignado_a === "object" ? asg.asignado_a : null) ||
                (asg.tecnico && typeof asg.tecnico === "object" ? asg.tecnico : null);

                let tecName =
                (tecObj &&
                    (tecObj.name ||
                    tecObj.full_name ||
                    tecObj.display_name ||
                    tecObj.email ||
                    tecObj.username)) ||
                asg.asignado_a_email ||
                "—";

                // si sólo hay id, intentar buscarlo en el listado de técnicos conocidos
                if (!tecObj && typeof asg.asignado_a === "number") {
                const found = optTecnicos.find((t) => String(t.value) === String(asg.asignado_a));
                if (found) tecName = found.label;
                else tecName = `Tec #${asg.asignado_a}`;
                }

                return (
                <tr
                    key={a.id}
                    style={{
                    borderTop: "1px solid #e5e7eb",
                    height: "48px", // ← altura de fila
                    lineHeight: "1.5em",
                    }}
                >
                    <td style={{ padding: "10px 12px" }}>{a.id}</td>
                    <td style={{ padding: "10px 12px" }}>{safeStr(asg.fecha)}</td>
                    <td style={{ padding: "10px 12px" }}>{safeStr(asg.direccion)}</td>
                    <td style={{ padding: "10px 12px" }}>{safeStr(asg.comuna)}</td>
                    <td style={{ padding: "10px 12px" }}>{safeStr(tecName)}</td>
                    <td style={{ padding: "10px 12px" }}>{safeStr(asg.marca)}</td>
                    <td style={{ padding: "10px 12px" }}>
                    <Link className={styles.button} to={`/admin/auditorias/${a.id}`}>
                        Ver detalles
                    </Link>
                    </td>
                </tr>
                );
            })}

            {!loading && filtered.length === 0 && (
                <tr>
                <td colSpan={7} className={styles.helper}>
                    No se encontraron resultados.
                </td>
                </tr>
            )}
            </tbody>

          </table>
        </div>
      </div>
    </div>
  );
}
