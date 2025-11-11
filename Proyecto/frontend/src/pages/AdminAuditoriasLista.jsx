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

// Endpoints “candidatos” para listar técnicos (cubre variantes de tu API)
const TECH_ENDPOINTS = [
  "/api/usuarios/?role=tecnico",
  "/auth/users/?role=tecnico",
  "/api/users/?role=tecnico",
  "/api/usuarios/",
  "/auth/users/",
  "/api/users/",
];

function normalizeUsers(raw) {
  const arr = asArray(raw);
  return arr
    .map((u) => {
      const id = u.id ?? u.pk ?? null;
      const role = (u.role ?? u.rol ?? "").toString().toLowerCase();
      const email = u.email ?? u.user?.email ?? u.username ?? "";
      const name =
        u.name ||
        (u.first_name || u.last_name ? `${u.first_name || ""} ${u.last_name || ""}`.trim() : "") ||
        u.full_name ||
        u.display_name ||
        "";
      const label = [name, email].filter(Boolean).join(" — ") || email || name || (id ? `Técnico #${id}` : "");
      if (!id) return null;
      return { id: String(id), role, label };
    })
    .filter(Boolean)
    .filter((t) => t.role === "tecnico" || !t.role); // si el endpoint no trae rol, igual lo aceptamos
}

export default function AdminAuditoriasLista() {
  const { user } = useAuth();
  const role = String(user?.rol || user?.role || "").toLowerCase();
  const isAdmin = role === "administrador";

  const [rows, setRows] = useState([]);         // auditorías (con asignación hidratada)
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // filtros
  const [q, setQ] = useState("");
  const [fTec, setFTec] = useState("");
  const [fCom, setFCom] = useState("");
  const [fMar, setFMar] = useState("");

  // opciones dinámicas
  const [optTecnicos, setOptTecnicos] = useState([{ value: "", label: "Todos los técnicos" }]);
  const [optComunas, setOptComunas] = useState([{ value: "", label: "Todas las comunas" }]);
  const [optMarcas, setOptMarcas] = useState([{ value: "", label: "Todas las marcas" }]);

  // mapa id -> label para resolver nombre del técnico
  const techLabelById = useMemo(() => {
    const map = {};
    for (const t of optTecnicos) {
      if (t.value) map[String(t.value)] = t.label;
    }
    return map;
  }, [optTecnicos]);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError("");
      try {
        // 1) Traer TODAS las auditorías (paginado DRF)
        let url = "/api/auditorias/";
        let acc = [];
        for (;;) {
          const res = await api.get(url);
          const chunk = asArray(res.data);
          acc = acc.concat(chunk);
          const next = res.data?.next;
          if (!next) break;
          url = next; // DRF entrega next absoluto
        }

        // 2) Hidratar asignaciones cuando vienen como id
        const needIds = Array.from(
          new Set(
            acc
              .map((a) => (typeof a.asignacion === "number" ? a.asignacion : null))
              .filter(Boolean)
          )
        );
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
        const hydrated = acc.map((a) => {
          if (ensureObj(a.asignacion)) return a;
          if (typeof a.asignacion === "number") {
            return { ...a, asignacion: idToAsign[a.asignacion] || { id: a.asignacion } };
          }
          return { ...a, asignacion: a.asignacion || {} };
        });
        setRows(hydrated);

        // 3) Construir set de valores para filtros básicos (comuna/marca)
        const comunasSet = new Set();
        const marcasSet = new Set();
        hydrated.forEach((a) => {
          const asg = a.asignacion || {};
          if (asg.comuna) comunasSet.add(String(asg.comuna));
          if (asg.marca) marcasSet.add(String(asg.marca));
        });
        setOptComunas([
          { value: "", label: "Todas las comunas" },
          ...Array.from(comunasSet.values()).sort().map((c) => ({ value: c, label: c })),
        ]);
        setOptMarcas([
          { value: "", label: "Todas las marcas" },
          ...Array.from(marcasSet.values()).sort().map((m) => ({ value: m, label: m })),
        ]);

        // 4) Armar catálogo de técnicos:
        //    a) desde los propios datos (ids vistos en asignaciones)
        const idsVistos = new Set();
        hydrated.forEach((a) => {
          const asg = a.asignacion || {};
          const tecObj = ensureObj(asg.asignado_a) || ensureObj(asg.tecnico);
          const tecId =
            (tecObj && (tecObj.id ?? tecObj.pk)) ||
            (typeof asg.asignado_a === "number" ? asg.asignado_a : null) ||
            null;
          if (tecId != null) idsVistos.add(String(tecId));
        });

        //    b) intentar obtener lista oficial de técnicos desde varios endpoints
        let catalogo = [];
        for (const ep of TECH_ENDPOINTS) {
          try {
            const r = await api.get(ep);
            catalogo = normalizeUsers(r.data);
            if (catalogo.length) break;
          } catch (_) {
            // probar el siguiente endpoint
          }
        }

        //    c) fusionar: ids vistos + catálogo oficial
        const mapa = new Map();
        // primero, del catálogo oficial
        for (const t of catalogo) {
          mapa.set(t.id, t.label);
        }
        // luego, garantizar ids vistos (aunque no tengamos el nombre real)
        idsVistos.forEach((id) => {
          if (!mapa.has(id)) mapa.set(id, `Técnico #${id}`);
        });

        const opcionesTecnicos = [{ value: "", label: "Todos los técnicos" }].concat(
          Array.from(mapa.entries()).map(([value, label]) => ({ value, label }))
        );
        setOptTecnicos(opcionesTecnicos);
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

      // filtrar por técnico (acepta id de select)
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

      // también dejamos buscar por nombre de técnico resuelto
      const tecIdPlano = typeof asg.asignado_a === "number" ? String(asg.asignado_a) : "";
      const tecObj = ensureObj(asg.asignado_a) || ensureObj(asg.tecnico);
      const tecNombrePlano =
        (tecObj &&
          (tecObj.name ||
            tecObj.full_name ||
            tecObj.display_name ||
            tecObj.email ||
            tecObj.username)) ||
        (tecIdPlano && techLabelById[tecIdPlano]) ||
        "";

      const bag = [
        asg.direccion,
        asg.comuna,
        asg.marca,
        asg.tecnologia,
        asg.id_vivienda,
        asg.rut_cliente,
        asg.fecha,
        tecNombrePlano,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      return bag.includes(txt);
    });
  }, [rows, q, fTec, fCom, fMar, techLabelById]);

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
            placeholder="Buscar dirección / id vivienda / rut / técnico…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <select className={styles.select} value={fTec} onChange={(e) => setFTec(e.target.value)}>
            {optTecnicos.map((o) => (
              <option key={o.value || "__all"} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
          <select className={styles.select} value={fCom} onChange={(e) => setFCom(e.target.value)}>
            {optComunas.map((o) => (
              <option key={o.value || "__all"} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
          <select className={styles.select} value={fMar} onChange={(e) => setFMar(e.target.value)}>
            {optMarcas.map((o) => (
              <option key={o.value || "__all"} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>

        {error && <div className={styles.error} style={{ marginTop: 8 }}>{error}</div>}
        {loading && <div className={styles.helper} style={{ marginTop: 8 }}>Cargando…</div>}

        <div style={{ overflowX: "auto", marginTop: 12 }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={{ whiteSpace: "nowrap" }}>ID</th>
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

                // Resolver nombre del técnico:
                // 1) si viene expandido
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
                  "";

                // 2) si solo hay id, buscar en el mapa de técnicos
                if (!tecObj && typeof asg.asignado_a === "number") {
                  const idStr = String(asg.asignado_a);
                  tecName = techLabelById[idStr] || `Técnico #${idStr}`;
                }

                return (
                  <tr
                    key={a.id}
                    style={{
                      borderTop: "1px solid #e5e7eb",
                      height: "48px",
                      lineHeight: "1.5em",
                    }}
                  >
                    <td style={{ padding: "10px 12px" }}>{a.id}</td>
                    <td style={{ padding: "10px 12px" }}>{safeStr(asg.fecha)}</td>
                    <td style={{ padding: "10px 12px" }}>{safeStr(asg.direccion)}</td>
                    <td style={{ padding: "10px 12px" }}>{safeStr(asg.comuna)}</td>
                    <td style={{ padding: "10px 12px" }}>{safeStr(tecName || "—")}</td>
                    <td style={{ padding: "10px 12px" }}>{safeStr(asg.marca)}</td>
                    <td style={{ padding: "10px 12px" }}>
                      {asgId ? (
                        <a className={styles.button} href={`/panel/auditorias/${asgId}/`}>
                          Ver detalles
                        </a>
                      ) : (
                        <button className={styles.button} disabled title="Sin asignación vinculada">
                          Ver detalles
                        </button>
                      )}
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