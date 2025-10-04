-- Extensiones y esquema opcional (puedes omitir el esquema si usas sólo "public")
CREATE EXTENSION IF NOT EXISTS pgcrypto;                -- para gen_random_uuid()
-- CREATE SCHEMA IF NOT EXISTS claro;
-- SET search_path TO claro, public;

-- Limpieza (orden correcto por dependencias)
DROP TABLE IF EXISTS evidencias_servicio CASCADE;
DROP TABLE IF EXISTS auditoria_categorias CASCADE;
DROP TABLE IF EXISTS auditoria_servicios CASCADE;
DROP TABLE IF EXISTS auditorias CASCADE;
DROP TABLE IF EXISTS reagendamientos CASCADE;
DROP TABLE IF EXISTS historial_visitas CASCADE;
DROP TABLE IF EXISTS asignaciones CASCADE;
DROP TABLE IF EXISTS direcciones CASCADE;
DROP TABLE IF EXISTS comunas CASCADE;
DROP TABLE IF EXISTS encuestas CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;

-- =========================
-- 1) USUARIOS (RUT opción B)
-- =========================
CREATE TABLE usuarios (
  rut_num TEXT NOT NULL CHECK (rut_num ~ '^[0-9]+$'),            -- solo dígitos
  dv      CHAR(1) NOT NULL CHECK (dv ~ '^[0-9Kk]$'),
  rut     TEXT GENERATED ALWAYS AS (rut_num || '-' || upper(dv)) STORED,
  nombre_usuario   TEXT NOT NULL,
  apellido_usuario TEXT NOT NULL,
  email_usuario    TEXT UNIQUE NOT NULL,
  contrasena_hash  TEXT NOT NULL,
  rol TEXT NOT NULL CHECK (rol IN ('tecnico','administrador')),        -- solo 2 roles
  fecha_creacion TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (rut)
);

-- =================================
-- 2) COMUNAS (con zona para filtros)
-- =================================
CREATE TABLE comunas (
  nombre TEXT PRIMARY KEY,
  zona   TEXT NOT NULL CHECK (zona IN ('norte','centro','sur'))
);

-- =====================================
-- 3) ENCUESTAS (catálogo/origen de base)
-- =====================================
CREATE TABLE encuestas (
  code   TEXT PRIMARY KEY,               -- p.ej. 'post_visita' | 'instalacion' | 'operaciones'
  nombre TEXT NOT NULL
);

INSERT INTO encuestas(code, nombre) VALUES
('post_visita','Post Visita'),
('instalacion','Instalación'),
('operaciones','Operaciones');

-- =====================================
-- 4) DIRECCIONES (identidad del domicilio)
-- =====================================
CREATE TABLE direcciones (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  rut_cliente TEXT,                      -- normalizado (opcional)
  id_vivienda TEXT UNIQUE,               -- si no hay uno, puede quedar NULL (entonces no aplica la unicidad)
  direccion   TEXT NOT NULL,
  comuna      TEXT REFERENCES comunas(nombre) ON DELETE RESTRICT
);

-- ==========================================================
-- 5) ASIGNACIONES (reemplaza a 'visitas' del esquema antiguo)
--    - 1 técnico puede tener muchas asignaciones
--    - 1 dirección NO puede tener >1 asignación ACTIVA simultánea
-- ==========================================================
CREATE TABLE asignaciones (
  id BIGSERIAL PRIMARY KEY,
  direccion_id UUID NOT NULL REFERENCES direcciones(id) ON DELETE RESTRICT,
  tecnico_rut  TEXT     REFERENCES usuarios(rut) ON DELETE RESTRICT,  -- NULL = sin asignar
  fecha  DATE NOT NULL,                                               -- CSV: fecha
  bloque TEXT CHECK (bloque IN ('10-13','14-18')),                    -- puede iniciar NULL y definirse luego
  tecnologia TEXT NOT NULL CHECK (tecnologia IN ('HFC','NFTT','FTTH')),
  marca      TEXT NOT NULL CHECK (marca IN ('CLARO','VTR')),
  encuesta_code TEXT NOT NULL REFERENCES encuestas(code) ON DELETE RESTRICT,
  id_qualtrics TEXT,                                                  -- trazabilidad externa
  estado TEXT NOT NULL CHECK (estado IN ('PENDIENTE','ASIGNADA','VISITADA','CANCELADA','REAGENDADA')),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Una dirección sólo puede tener UNA asignación ACTIVA (pendiente/asignada/reagendada)
CREATE UNIQUE INDEX uniq_asignacion_direccion_activa
  ON asignaciones(direccion_id)
  WHERE estado IN ('PENDIENTE','ASIGNADA','REAGENDADA');

CREATE INDEX ix_asignaciones_tecnico   ON asignaciones(tecnico_rut);
CREATE INDEX ix_asignaciones_estado    ON asignaciones(estado);
CREATE INDEX ix_asignaciones_fecha     ON asignaciones(fecha);
CREATE INDEX ix_asignaciones_filtros   ON asignaciones(marca, tecnologia, encuesta_code);

-- ======================================================
-- 6) REAGENDAMIENTOS (histórico "antes -> después")
--    * NO lo manda el cliente: se toma "anterior" desde asignaciones
-- ======================================================
CREATE TABLE reagendamientos (
  id BIGSERIAL PRIMARY KEY,
  asignacion_id BIGINT NOT NULL REFERENCES asignaciones(id) ON DELETE CASCADE,
  fecha_anterior  DATE NOT NULL,
  bloque_anterior TEXT CHECK (bloque_anterior IN ('10-13','14-18')),
  fecha_nueva     DATE NOT NULL,
  bloque_nuevo    TEXT NOT NULL CHECK (bloque_nuevo IN ('10-13','14-18')),
  motivo          TEXT NOT NULL,
  usuario_rut     TEXT NOT NULL REFERENCES usuarios(rut) ON DELETE RESTRICT, -- quién ejecuta el cambio
  created_at      TIMESTAMPTZ DEFAULT now()
);

-- ======================================
-- 7) HISTORIAL (auditoría de acciones)
-- ======================================
CREATE TABLE historial_visitas (
  id BIGSERIAL PRIMARY KEY,
  asignacion_id BIGINT NOT NULL REFERENCES asignaciones(id) ON DELETE CASCADE,
  accion TEXT NOT NULL CHECK (accion IN ('creada','asignada','reagendada','cerrada','completada','estado_cambiado','auditoria_creada')),
  detalles TEXT,
  usuario_rut TEXT NOT NULL REFERENCES usuarios(rut) ON DELETE RESTRICT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ===================================================
-- 8) AUDITORIAS (formulario cuando el cliente autoriza
--    o cuando hay problemas; estructura flexible)
-- ===================================================
CREATE TABLE auditorias (
  id BIGSERIAL PRIMARY KEY,
  asignacion_id BIGINT NOT NULL REFERENCES asignaciones(id) ON DELETE RESTRICT,
  estado_cliente TEXT NOT NULL CHECK (estado_cliente IN ('autoriza','sin_moradores','rechaza','contingencia','masivo','reagendo')),
  ont_modem_ok BOOLEAN,                    -- Q72

  -- Bloques del cuestionario (JSON) para no rigidizar la DB (Q16..Q32)
  bloque_agendamiento JSONB,
  bloque_llegada      JSONB,
  bloque_proceso      JSONB,
  bloque_config       JSONB,
  bloque_cierre       JSONB,
  percepcion          JSONB,

  descripcion_problema TEXT,               -- Q12 / Q73 HFC
  fotos JSONB,                             -- Q13..Q15 (paths)
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Q8: Servicio con problema (multiselección)
CREATE TABLE auditoria_servicios (
  id BIGSERIAL PRIMARY KEY,
  auditoria_id BIGINT NOT NULL REFERENCES auditorias(id) ON DELETE CASCADE,
  servicio TEXT NOT NULL CHECK (servicio IN ('internet','tv','fono','otro'))
);

-- Q9/Q10: Categorías por servicio (Internet/TV); "Otro" se documenta en texto
CREATE TABLE auditoria_categorias (
  id BIGSERIAL PRIMARY KEY,
  auditoria_servicio_id BIGINT NOT NULL REFERENCES auditoria_servicios(id) ON DELETE CASCADE,
  categoria TEXT NOT NULL,
  extra     TEXT
);

-- =======================================
-- 9) EVIDENCIAS (archivos individuales)
-- =======================================
CREATE TABLE evidencias_servicio (
  id BIGSERIAL PRIMARY KEY,
  auditoria_id  BIGINT REFERENCES auditorias(id) ON DELETE CASCADE,
  asignacion_id BIGINT NOT NULL REFERENCES asignaciones(id) ON DELETE CASCADE,
  tipo TEXT NOT NULL CHECK (tipo IN ('foto','firma','comprobante','otro')) DEFAULT 'foto',
  archivo_ruta TEXT NOT NULL,
  descripcion  TEXT,
  usuario_rut  TEXT NOT NULL REFERENCES usuarios(rut) ON DELETE RESTRICT,
  created_at   TIMESTAMPTZ DEFAULT now()
);
